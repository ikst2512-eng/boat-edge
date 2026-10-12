#!/usr/bin/env python3
"""V320 read-only SITE V232 baseline adapter for V319 paired research.

Requires explicit source file, validates saved predeadline snapshot metadata.
A local saved timestamp is NOT independent proof of GitHub first receipt.
Never reads results or authorizes scoring/promotion.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path

from boat_edge_v319_pre_result_pair import valid_tickets
from boat_edge_v318_shadow_freeze import KEY, parse_time, canonical

JST = timezone(timedelta(hours=9))


def baseline_from_v232(record):
    if not isinstance(record, dict):
        raise ValueError("INVALID_V232_RECORD")
    key = record.get("race_key")
    if not isinstance(key, str) or KEY.fullmatch(key) is None:
        raise ValueError("INVALID_RACE_KEY")
    if record.get("scope") != "SITE_REFERENCE_UNSEEN_PRE_RESULT_ONLY_NOT_FORMAL_FRESH":
        raise ValueError("NOT_SITE_REFERENCE_PRE_RESULT")
    if record.get("formal_results_seen") is not False or record.get("formal_gate_unlocked") is not False:
        raise ValueError("FORMAL_LOCK_NOT_VERIFIED")
    if record.get("production_accuracy_claim") is not False or record.get("real_purchases_authorized") is not False:
        raise ValueError("PRODUCTION_OR_WAGER_CLAIM")
    deadline = parse_time(record.get("deadline_jst"))
    raw_time = record.get("evidence_committed_at")
    if not isinstance(raw_time, str):
        raise ValueError("MISSING_EVIDENCE_COMMIT_TIME")
    committed = datetime.fromisoformat(raw_time.replace("Z", "+00:00"))
    if committed.tzinfo is None or committed >= deadline:
        raise ValueError("NOT_PREDEADLINE")
    tickets = valid_tickets(record.get("top10"))
    for size in (3, 5):
        subset = record.get("top" + str(size))
        if not isinstance(subset, list) or subset != tickets[:size]:
            raise ValueError("TOP_N_NOT_PREFIX_OF_TOP10")
    if record.get("head_top1") != tickets[0].split("-")[0]:
        raise ValueError("HEAD_TOP1_MISMATCH")
    if not isinstance(record.get("model_id"), str) or not record["model_id"]:
        raise ValueError("MISSING_BASELINE_MODEL_ID")
    return {
        "race_key": key,
        "model_id": record["model_id"],
        "deadline_jst": deadline.isoformat(),
        "frozen_at_jst": committed.astimezone(JST).isoformat(),
        "entry_basis": "BOAT_NUMBER",
        "top10_boat": list(tickets),
        "original_site_record_sha256": hashlib.sha256(canonical(record)).hexdigest(),
        "site_timestamp_self_reported_not_git_server_attested": True,
        "source_independently_authenticated": False,
        "results_read": False,
        "formal_fresh_read": False,
    }


def main():
    parser = argparse.ArgumentParser(description="Convert saved V232 pre-result Top10 to V319 input")
    parser.add_argument("--input", type=Path, required=True)
    args = parser.parse_args()
    record = json.loads(args.input.read_text(encoding="utf-8"))
    print(json.dumps(baseline_from_v232(record), ensure_ascii=False, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
