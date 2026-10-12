#!/usr/bin/env python3
"""V328 single-command, live-only SITE research candidate and immutable freeze.

Uses only existing pre-result race JSON and three local V315 source receipts.
No retroactive freeze: requires live JST clock BEFORE deadline. V316 audits
receipts; V312 builds 120-way provisional-exhibition research candidates;
V318 writes once. Never reads formal Fresh, results, odds or payouts.
"""
from __future__ import annotations

import argparse
from datetime import datetime
import hashlib
import json
from pathlib import Path

from boat_edge_v312_pre_result_ablation import build_shadow
from boat_edge_v316_receipt_assemble import assemble
from boat_edge_v318_shadow_freeze import JST, KEY, freeze_file, parse_time


def live_research_freeze(root, race_key, now=None):
    if not isinstance(race_key, str) or KEY.fullmatch(race_key) is None:
        raise ValueError("INVALID_RACE_KEY")
    root = root.resolve()
    race_path = root / "data" / "races" / (race_key + ".json")
    if race_path.is_symlink():
        raise ValueError("RACE_SYMLINK_FORBIDDEN")
    race_raw = race_path.read_bytes()
    race = json.loads(race_raw)
    if race.get("race_key") != race_key:
        raise ValueError("RACE_KEY_MISMATCH")
    meta = race.get("meta")
    if not isinstance(meta, dict) or meta.get("phase") != "PRE_RESULT":
        raise ValueError("PRE_RESULT_RACE_REQUIRED")
    if any(meta.get(k) is not False for k in ("results_seen", "unlock", "scoring")):
        raise ValueError("RESULT_OR_UNLOCK_FLAG_FORBIDDEN")
    if not isinstance(meta.get("date"), str) or meta["date"].replace("-", "") != race_key[:8]:
        raise ValueError("RACE_DATE_MISMATCH")
    deadline_hhmm = meta.get("deadline")
    if not isinstance(deadline_hhmm, str) or len(deadline_hhmm) != 5:
        raise ValueError("DEADLINE_TIME_MISSING")
    deadline_jst = meta["date"] + "T" + deadline_hhmm + ":00+09:00"
    deadline = parse_time(deadline_jst)
    now = now if now is not None else datetime.now(JST)
    if not isinstance(now, datetime) or now.tzinfo is None or now.utcoffset() is None:
        raise ValueError("AWARE_CLOCK_REQUIRED")
    now = now.astimezone(JST)
    if now >= deadline:
        raise ValueError("LIVE_WINDOW_CLOSED_NO_BACKFILL")
    # A race file updated after deadline is never allowed as an as-of snapshot.
    updated_at = meta.get("updated_at")
    if not isinstance(updated_at, str):
        raise ValueError("RACE_UPDATED_AT_REQUIRED")
    try:
        updated = datetime.fromisoformat(updated_at)
    except ValueError as exc:
        raise ValueError("RACE_UPDATED_AT_INVALID") from exc
    if updated.tzinfo is None or updated >= deadline or updated > now:
        raise ValueError("RACE_FILE_TIMESTAMP_NOT_PREDEADLINE")
    source_audit = race.get("source_audit")
    if not isinstance(source_audit, dict):
        raise ValueError("SOURCE_AUDIT_REQUIRED")
    for provider in ("race_card", "beforeinfo"):
        entry = source_audit.get(provider)
        if not isinstance(entry, dict) or entry.get("status") != "ok":
            raise ValueError("REQUIRED_SOURCE_MISSING:" + provider)
        try:
            fetched = datetime.fromisoformat(entry["fetched_at"])
        except (KeyError, ValueError, TypeError) as exc:
            raise ValueError("SOURCE_FETCH_TIMESTAMP_MISSING:" + provider) from exc
        if fetched.tzinfo is None or fetched >= deadline or fetched > now:
            raise ValueError("SOURCE_FETCH_NOT_PREDEADLINE:" + provider)
    candidate = build_shadow(race)
    # Bind the exact race input bytes into the immutable V318 candidate digest.
    candidate["race_source_sha256"] = hashlib.sha256(race_raw).hexdigest()
    report = assemble(root, race_key, deadline_jst)
    if not report["ready_for_research_review"]:
        raise ValueError("THREE_SOURCE_RECEIPTS_NOT_READY")
    result = freeze_file(root, report, candidate, now)
    result["race_source_sha256"] = hashlib.sha256(race_raw).hexdigest()
    result["three_source_original_exhibition_values_verified"] = False
    result["actual_entry_independently_verified"] = False
    result["accuracy_improvement_proven"] = False
    result["production_eligible"] = False
    return result


def main():
    parser = argparse.ArgumentParser(description="Live-only pre-result SITE research freeze")
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--race-key", required=True)
    args = parser.parse_args()
    print(json.dumps(live_research_freeze(args.root, args.race_key),
                     ensure_ascii=False, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
