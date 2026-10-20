#!/usr/bin/env python3
"""Read-only race-source audit. No network, workflow triggers, or prediction writes."""
import argparse
from collections import Counter
from datetime import datetime, timezone, timedelta
import json
from pathlib import Path
import re

FIELDS = ("race_card", "beforeinfo", "original_exhibition", "odds")
KEY = re.compile(r"^(20\d{6})-(0[1-9]|1\d|2[0-4])-(0[1-9]|1[0-2])$")
JST = timezone(timedelta(hours=9))


def audit(root, day):
    counts = {field: Counter() for field in FIELDS}
    rows = []
    for path in sorted((root / "data" / "races").glob(day + "-*.json")):
        if not KEY.fullmatch(path.stem):
            continue
        try:
            obj = json.loads(path.read_text(encoding="utf-8"))
            if obj.get("race_key") != path.stem:
                raise ValueError("race_key mismatch")
            src = obj.get("source_audit") or {}
            meta = obj.get("meta") or {}
            statuses = {}
            for field in FIELDS:
                entry = src.get(field)
                status = (entry or {}).get("status", "not_recorded") if isinstance(entry, dict) else "not_recorded"
                if status == "ok" and field == "beforeinfo":
                    cov = entry.get("six_boat_coverage") or {}
                    if not cov.get("six_boat_complete"):
                        status = "incomplete_exhibition"
                statuses[field] = status
                counts[field][status] += 1
            rows.append({"race_key": path.stem, "venue": meta.get("venue"),
                         "deadline": meta.get("deadline"), "statuses": statuses})
        except (OSError, ValueError, TypeError) as error:
            rows.append({"race_key": path.stem, "error": type(error).__name__})
            for field in FIELDS:
                counts[field]["invalid_record"] += 1
    # This denominator includes only saved cards, not all scheduled races.
    n = len(rows)
    summary = {}
    for field in FIELDS:
        success = counts[field]["ok"]
        summary[field] = {"saved_races": n, "confirmed_ok": success,
                          "saved_card_success_percent": round(100 * success / n, 2) if n else None,
                          "by_status": dict(sorted(counts[field].items()))}
    return {
        "schema": "BOAT_EDGE_02_READONLY_SOURCE_COVERAGE_V1",
        "date_jst": day, "generated_at_jst": datetime.now(JST).isoformat(),
        "venues_total": 24, "saved_venues": len({r["race_key"][9:11] for r in rows}),
        "saved_races": n, "expected_scheduled_races": None,
        "all_scheduled_race_success_percent": None,
        "note": "Saved-card rate only; missing scheduled races, live source verification and original exhibition values are not proven.",
        "summary": summary, "rows": rows,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--day", required=True, help="JST date in YYYYMMDD")
    parser.add_argument("--output", type=Path, help="Optional explicit report destination")
    args = parser.parse_args()
    if not re.fullmatch(r"20\d{6}", args.day):
        parser.error("--day must be YYYYMMDD")
    report = audit(args.root, args.day)
    serialized = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(serialized, encoding="utf-8")
    else:
        print(serialized, end="")


if __name__ == "__main__":
    main()
