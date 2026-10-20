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


def load_expected(path, day):
    """An independently supplied schedule, never inferred from saved cards."""
    if path is None:
        return None
    document = json.loads(path.read_text(encoding="utf-8"))
    keys = document.get("race_keys")
    if document.get("date_jst") != day or not isinstance(keys, list):
        raise ValueError("schedule date or race_keys invalid")
    if any(not isinstance(key, str) or not KEY.fullmatch(key) or key[:8] != day for key in keys):
        raise ValueError("schedule includes invalid or wrong-day race keys")
    if not keys:
        raise ValueError("empty independent schedule not accepted")
    if len(set(keys)) != len(keys):
        raise ValueError("duplicate scheduled race")
    return set(keys)


def retry_candidates(rows, day, now=None):
    """Diagnostics only: never execute fetches or bypass deadline locks."""
    now = now or datetime.now(JST)
    if now.tzinfo is None or now.utcoffset() is None:
        raise ValueError("aware JST clock required")
    now = now.astimezone(JST)
    candidates = []
    for row in rows:
        key = row["race_key"]
        deadline = row.get("deadline")
        if row.get("error") or not isinstance(deadline, str) or not re.fullmatch(r"\d{2}:\d{2}", deadline):
            continue
        try:
            due = datetime.strptime(day + deadline, "%Y%m%d%H:%M").replace(tzinfo=JST)
        except ValueError:
            continue
        if due <= now:
            continue
        statuses = row.get("statuses", {})
        for field in ("race_card", "beforeinfo"):
            if statuses.get(field) not in ("ok",):
                candidates.append({"race_key": key, "source": field,
                                   "reason": statuses.get(field, "not_recorded"),
                                   "deadline_jst": due.isoformat(),
                                   "automatic_fetch_authorized": False})
    return candidates


def audit(root, day, expected=None, now=None):
    counts = {field: Counter() for field in FIELDS}
    rows = []
    for path in sorted((root / "data" / "races").glob(day + "-*.json")):
        if not KEY.fullmatch(path.stem):
            continue
        try:
            obj = json.loads(path.read_text(encoding="utf-8"))
            if obj.get("race_key") != path.stem:
                raise ValueError("race_key mismatch")
            if not isinstance(obj, dict):
                raise ValueError("invalid race object")
            src = obj.get("source_audit") or {}
            meta = obj.get("meta") or {}
            if not isinstance(src, dict) or not isinstance(meta, dict):
                raise ValueError("invalid audit/meta structure")
            if (meta.get("date") not in (None, day[:4] + "-" + day[4:6] + "-" + day[6:])
                    or str(meta.get("venue_code", path.stem[9:11])).zfill(2) != path.stem[9:11]
                    or meta.get("phase") not in (None, "PRE_RESULT")):
                raise ValueError("race meta identity or phase mismatch")
            statuses = {}
            for field in FIELDS:
                entry = src.get(field)
                status = (entry or {}).get("status", "not_recorded") if isinstance(entry, dict) else "not_recorded"
                if status == "ok" and not (isinstance(entry, dict) and entry.get("sha256") and entry.get("fetched_at")):
                    status = "unverified_ok"
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
    saved_keys = {row["race_key"] for row in rows if "error" not in row}
    valid_rows = [row for row in rows if "error" not in row]
    missing = sorted(expected - saved_keys) if expected is not None else None
    unexpected = sorted(saved_keys - expected) if expected is not None else None
    # A saved race does not by itself establish data-source completeness.
    n = len(rows)
    summary = {}
    for field in FIELDS:
        success = counts[field]["ok"]
        summary[field] = {"saved_races": n, "confirmed_ok": success,
                          "saved_card_success_percent": round(100 * success / n, 2) if n else None,
                          "by_status": dict(sorted(counts[field].items())),
                          "scheduled_recorded_ok_percent": (
                              round(100 * sum(
                                  1 for row in rows
                                  if row["race_key"] in expected
                                  and row.get("statuses", {}).get(field) == "ok"
                              ) / len(expected), 2)
                              if expected else None)}
    return {
        "schema": "BOAT_EDGE_02_READONLY_SOURCE_COVERAGE_V1",
        "date_jst": day, "generated_at_jst": datetime.now(JST).isoformat(),
        "venues_total": 24, "saved_venues": len({r["race_key"][9:11] for r in valid_rows}),
        "saved_races": n,
        "expected_scheduled_races": len(expected) if expected is not None else None,
        "missing_scheduled_race_keys": missing,
        "unexpected_saved_race_keys": unexpected,
        "scheduled_card_presence_percent": (
            round(100 * len(saved_keys & expected) / len(expected), 2)
            if expected else None),
        "all_scheduled_race_success_percent": None,
        "note": "Saved-card rate only; missing scheduled races, live source verification and original exhibition values are not proven.",
        "summary": summary, "retry_candidates_diagnostics_only": retry_candidates(rows, day, now), "rows": rows,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--day", required=True, help="JST date in YYYYMMDD")
    parser.add_argument("--output", type=Path, help="Optional explicit report destination")
    parser.add_argument("--schedule", type=Path,
                        help="Trusted independent JSON schedule: date_jst and race_keys")
    args = parser.parse_args()
    if not re.fullmatch(r"20\d{6}", args.day):
        parser.error("--day must be YYYYMMDD")
    try:
        expected = load_expected(args.schedule, args.day)
    except (OSError, ValueError, TypeError) as exc:
        parser.error("invalid schedule: " + str(exc))
    report = audit(args.root, args.day, expected)
    serialized = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(serialized, encoding="utf-8")
    else:
        print(serialized, end="")


if __name__ == "__main__":
    main()
