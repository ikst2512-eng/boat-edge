#!/usr/bin/env python3
"""V311 read-only PRE_RESULT provenance audit of existing data/races JSON.

This does NOT authenticate source bytes, fetch pages, inspect outcomes, score
predictions, or treat start-exhibition entry as actual race entry.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import re

JST = timezone(timedelta(hours=9))
RACE_KEY = re.compile(r"^20[0-9]{6}-(?:0[1-9]|1[0-9]|2[0-4])-(?:0[1-9]|1[0-2])$")
CLOCK = re.compile(r"^(?:[01][0-9]|2[0-3]):[0-5][0-9]$")
SHA = re.compile(r"^[0-9a-f]{64}$")
SOURCES = ("race_card", "beforeinfo", "stt", "tkz", "sui", "original_exhibition")


def timestamp(s):
    if not isinstance(s, str):
        return None
    try:
        dt = datetime.fromisoformat(s)
        return dt.astimezone(JST) if dt.tzinfo is not None else None
    except (ValueError, OverflowError):
        return None


def audit_race(race):
    if not isinstance(race, dict):
        raise ValueError("INVALID_RACE_DOCUMENT")
    key = race.get("race_key")
    meta = race.get("meta")
    meta = meta if isinstance(meta, dict) else {}
    clock = meta.get("deadline")
    if not isinstance(key, str) or RACE_KEY.fullmatch(key) is None or not isinstance(clock, str) or CLOCK.fullmatch(clock) is None:
        raise ValueError("RACE_KEY_OR_DEADLINE_INVALID")
    try:
        deadline = datetime.strptime(key[:8] + clock, "%Y%m%d%H:%M").replace(tzinfo=JST)
    except ValueError as exc:
        raise ValueError("DEADLINE_INVALID") from exc
    audit = race.get("source_audit")
    audit = audit if isinstance(audit, dict) else {}
    sources = {}
    for name in SOURCES:
        row = audit.get(name)
        row = row if isinstance(row, dict) else {}
        when = timestamp(row.get("fetched_at"))
        sha = row.get("sha256")
        qualified = (row.get("status") == "ok" and isinstance(row.get("source"), str)
                     and row["source"].startswith("https://")
                     and isinstance(sha, str) and SHA.fullmatch(sha) is not None
                     and when is not None and when < deadline)
        sources[name] = {
            "pre_deadline_metadata_qualified": bool(qualified),
            "reported_status": row.get("status", "absent"),
            "source_url_present": isinstance(row.get("source"), str) and row["source"].startswith("https://"),
            "sha256_recorded": isinstance(sha, str) and SHA.fullmatch(sha) is not None,
            "fetched_before_deadline": when is not None and when < deadline,
            "source_bytes_independently_verified": False,
        }
    exhibition = (race.get("beforeinfo") or {}).get("start_exhibition") if isinstance(race.get("beforeinfo"), dict) else None
    candidate = []
    if isinstance(exhibition, list) and len(exhibition) == 6:
        for row in exhibition:
            if isinstance(row, dict) and type(row.get("lane")) is int and type(row.get("course")) is int:
                candidate.append((row["lane"], row["course"]))
    permutation = (len(candidate) == 6 and {boat for boat, _ in candidate} == set(range(1, 7))
                   and {course for _, course in candidate} == set(range(1, 7)))
    # The existing actual_entry field mirrors exhibition ST; do not use it as
    # independent proof of actual-course entry, even when lanes happen to match.
    independently_verified_actual_course = False
    reasons = []
    if not sources["race_card"]["pre_deadline_metadata_qualified"]:
        reasons.append("RACE_CARD_NOT_PREDEADLINE_PROVEN")
    if not sources["beforeinfo"]["pre_deadline_metadata_qualified"]:
        reasons.append("BEFOREINFO_NOT_PREDEADLINE_PROVEN")
    if not permutation:
        reasons.append("START_EXHIBITION_COURSE_MISSING_OR_INVALID")
    reasons.append("ACTUAL_COURSE_NOT_INDEPENDENTLY_VERIFIED")
    reasons.append("BOATERS_ORIGINAL_EXHIBITION_NOT_INDEPENDENTLY_VERIFIED")
    reasons.append("KYOTEIBIYORI_ORIGINAL_EXHIBITION_NOT_INDEPENDENTLY_VERIFIED")
    return {
        "race_key": key,
        "deadline_jst": deadline.isoformat(),
        "source_metadata": sources,
        "start_exhibition_course_permutation_recorded": bool(permutation),
        "entry_semantics": "START_EXHIBITION_NOT_ACTUAL_ENTRY",
        "actual_course_independently_verified": independently_verified_actual_course,
        "boaters_verified": False,
        "kyoteibiyori_verified": False,
        "ready_for_v308_actual_course_research": False,
        "source_bytes_reauthenticated": False,
        "reasons": reasons,
        "results_accessed": False,
        "formal_fresh_accessed": False,
    }


def audit_directory(directory):
    if not directory.is_dir():
        raise ValueError("RACE_DIRECTORY_NOT_FOUND")
    rows = []
    errors = []
    for path in sorted(directory.glob("*.json")):
        try:
            doc = json.loads(path.read_text(encoding="utf-8"))
            rows.append(audit_race(doc))
        except (OSError, UnicodeError, ValueError, TypeError, KeyError) as exc:
            errors.append({"file": path.name, "reason": str(exc)})
    return {
        "model_id": "BOAT_EDGE_V311_EXISTING_RACE_PROVENANCE_AUDIT",
        "inspected": len(rows),
        "invalid": len(errors),
        "ready_for_v308": sum(bool(row["ready_for_v308_actual_course_research"]) for row in rows),
        "beforeinfo_predeadline_metadata": sum(bool(row["source_metadata"]["beforeinfo"]["pre_deadline_metadata_qualified"]) for row in rows),
        "exhibition_course_permutations": sum(bool(row["start_exhibition_course_permutation_recorded"]) for row in rows),
        "rows": rows,
        "errors": errors,
        "actual_race_results_read": False,
        "formal_fresh_accessed": False,
    }


def main():
    parser = argparse.ArgumentParser(description="Audit metadata only; never score or fetch results")
    parser.add_argument("--race-dir", type=Path, required=True)
    parser.add_argument("--summary-only", action="store_true")
    args = parser.parse_args()
    report = audit_directory(args.race_dir)
    if args.summary_only:
        report.pop("rows")
    print(json.dumps(report, sort_keys=True, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
