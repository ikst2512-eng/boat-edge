#!/usr/bin/env python3
"""Apply an independently collected, validated PRE_RESULT enrichment.

Does not fetch or manufacture data. Produces a new snapshot; never overwrites
an existing file, changes score/unlock flags, or touches result endpoints.

Usage: python tools/apply_pre_result_enrichment.py RACE.json ENRICHMENT.json OUTPUT.json
"""
import argparse
import json
import os
import tempfile
from pathlib import Path

from validate_pre_result_enrichment import validate


def apply(race, enrichment, now=None):
    report = validate(race, enrichment, now=now)
    if not report["ok"]:
        raise ValueError("enrichment rejected: " + ",".join(report["reasons"]))
    # Never replace a previously recorded field, even if a later enrichment
    # passes schema checks. Preserve the first immutable pre-result record.
    for field in ("actual_entry", "course_stats"):
        if field not in enrichment:
            continue
        if field == "actual_entry" and race.get("actual_entry"):
            raise ValueError("actual_entry already recorded; replacement forbidden")
        if field == "course_stats" and any("course_stats" in r for r in race.get("racers", [])):
            raise ValueError("course_stats already recorded; replacement forbidden")
        if field in (race.get("source_audit") or {}):
            raise ValueError(field + " source audit already recorded; replacement forbidden")
    merged = json.loads(json.dumps(race))
    if "actual_entry" in enrichment:
        merged["actual_entry"] = enrichment["actual_entry"]
    if "course_stats" in enrichment:
        by_registration = {str(r["registration_no"]): r for r in enrichment["course_stats"]}
        for racer in merged["racers"]:
            racer["course_stats"] = {
                field: by_registration[str(racer["registration_no"])][field]
                for field in ("course", "first_rate", "second_rate", "third_rate")
            }
    merged.setdefault("source_audit", {}).update({
        kind: enrichment["source_audit"][kind]
        for kind in ("actual_entry", "course_stats")
        if kind in enrichment
    })
    # No result-derived flags or model changes are permitted.
    for field in ("results_seen", "unlock", "scoring", "phase"):
        if merged["meta"].get(field) != race["meta"].get(field):
            raise ValueError("mutated protected flag " + field)
    return merged



def write_new_snapshot(output, updated):
    """Atomically create a fresh snapshot; never modify a previous file."""
    output = Path(output)
    if output.exists():
        raise FileExistsError("output exists; overwrite is forbidden")
    output.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=".enrichment-", dir=str(output.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(updated, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
        os.link(tmp, output)
    finally:
        os.unlink(tmp)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("race", type=Path)
    p.add_argument("enrichment", type=Path)
    p.add_argument("output", type=Path)
    args = p.parse_args()
    if args.output.resolve() in (args.race.resolve(), args.enrichment.resolve()):
        p.error("output must differ from both inputs")
    if args.output.exists():
        p.error("output exists; overwrite is forbidden")
    race = json.loads(args.race.read_text(encoding="utf-8"))
    addition = json.loads(args.enrichment.read_text(encoding="utf-8"))
    updated = apply(race, addition)
    write_new_snapshot(args.output, updated)
    print(json.dumps({"ok": True, "output": str(args.output), "race_key": race["race_key"],
                      "added": [k for k in ("actual_entry", "course_stats") if k in addition]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
