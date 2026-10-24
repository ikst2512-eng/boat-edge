#!/usr/bin/env python3
"""Capture imminent PRE_RESULT evidence in a bounded, fail-closed scheduled batch.

Scans only today's data/races/*.json, excludes past deadlines and non-locked
races. Captures official beforeinfo source and its SHA256 audit as paired
files in a new output directory. Does not modify race data or infer entries.
"""
import argparse
import datetime as dt
import json
from pathlib import Path

from archive_pre_result_source import JST, archive


def eligible(path, now):
    try:
        race = json.loads(path.read_text(encoding="utf-8"))
        meta = race.get("meta", {})
        if meta.get("date") != now.date().isoformat() or meta.get("phase") != "PRE_RESULT":
            return None
        if any(meta.get(k) is not False for k in ("results_seen", "scoring", "unlock")):
            return None
        deadline = dt.datetime.fromisoformat(meta["date"] + "T" + meta["deadline"] + ":00+09:00")
        minutes = (deadline - now).total_seconds() / 60
        if not 3 <= minutes <= 35:
            return None
        key = race.get("race_key", "")
        if path.stem != key:
            return None
        return deadline, race
    except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError):
        return None


def batch(race_dir, output, now=None, maximum=12, capture=archive):
    now = now or dt.datetime.now(JST)
    matches = []
    for path in sorted(Path(race_dir).glob(now.strftime("%Y%m%d") + "-*.json")):
        result = eligible(path, now)
        if result:
            matches.append((*result, path))
    matches.sort(key=lambda item: item[0])
    report = {"checked": len(matches), "captured": [], "skipped": [], "failed": []}
    for deadline, race, path in matches[:maximum]:
        key = race["race_key"]
        if (Path(output) / (key + ".beforeinfo.html")).exists():
            report["skipped"].append({"key": key, "reason": "already_captured"})
            continue
        try:
            audit = capture(race, output)
            report["captured"].append({"key": key, "sha256": audit["sha256"]})
        except (OSError, ValueError, TimeoutError) as exc:
            report["failed"].append({"key": key, "reason": type(exc).__name__})
    return report


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--races", type=Path, default=Path("data/races"))
    p.add_argument("--output", type=Path, default=Path("artifacts/pre-result-captures"))
    p.add_argument("--maximum", type=int, default=12)
    args = p.parse_args()
    if not 1 <= args.maximum <= 24:
        p.error("maximum must be from 1 to 24")
    report = batch(args.races, args.output, maximum=args.maximum)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 1 if report["failed"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
