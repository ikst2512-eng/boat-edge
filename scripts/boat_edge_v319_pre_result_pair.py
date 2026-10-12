#!/usr/bin/env python3
"""V319 read-only paired PRE_RESULT Top10 overlap audit.

Does NOT load outcomes, score accuracy, compare returns or infer improvement.
Only accepts a previously frozen research V318 record and a separately
frozen site baseline with matching race identity and predeadline timestamps.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timedelta
import hashlib
import json
from pathlib import Path

from boat_edge_v318_shadow_freeze import KEY, canonical, parse_time

MODEL = "BOAT_EDGE_V319_PRE_RESULT_TOP10_OVERLAP_ONLY"


def valid_tickets(tickets):
    if not isinstance(tickets, list) or len(tickets) != 10 or len(set(tickets)) != 10:
        raise ValueError("TOP10_MUST_HAVE_TEN_DISTINCT_TICKETS")
    for ticket in tickets:
        if not isinstance(ticket, str):
            raise ValueError("INVALID_TICKET")
        parts = ticket.split("-")
        if len(parts) != 3 or any(len(x) != 1 or x not in "123456" for x in parts) or len(set(parts)) != 3:
            raise ValueError("INVALID_TICKET")
    return tickets


def compare(shadow, baseline):
    if not isinstance(shadow, dict) or not isinstance(baseline, dict):
        raise ValueError("INVALID_INPUT")
    if shadow.get("model_id") != "BOAT_EDGE_V318_SHADOW_FREEZE_RESEARCH_ONLY":
        raise ValueError("V318_FREEZE_REQUIRED")
    key = shadow.get("race_key")
    if not isinstance(key, str) or KEY.fullmatch(key) is None or baseline.get("race_key") != key:
        raise ValueError("SAME_RACE_REQUIRED")
    deadline = parse_time(shadow.get("deadline_jst"))
    shadow_time = parse_time(shadow.get("frozen_at_jst"))
    baseline_time = parse_time(baseline.get("frozen_at_jst"))
    if shadow_time >= deadline or baseline_time >= deadline:
        raise ValueError("BOTH_FREEZES_MUST_PRECEDE_DEADLINE")
    if shadow.get("results_read") is not False or shadow.get("formal_fresh_read") is not False:
        raise ValueError("SHADOW_RESULT_GUARD_REQUIRED")
    if baseline.get("results_read") is not False or baseline.get("formal_fresh_read") is not False:
        raise ValueError("BASELINE_RESULT_GUARD_REQUIRED")
    if baseline.get("entry_basis") != "BOAT_NUMBER":
        raise ValueError("BASELINE_TICKETS_MUST_BE_BOAT_NUMBERS")
    modes = shadow.get("research_top10_by_mode")
    if not isinstance(modes, dict) or not modes:
        raise ValueError("RESEARCH_MODES_REQUIRED")
    baseline_top10 = valid_tickets(baseline.get("top10_boat"))
    base_set = set(baseline_top10)
    overlaps = {}
    for name, tickets in modes.items():
        valid_tickets(tickets)
        common = [ticket for ticket in tickets if ticket in base_set]
        overlaps[name] = {
            "overlap_count": len(common),
            "shared_tickets": common,
            "research_only_tickets": [ticket for ticket in tickets if ticket not in base_set],
            "baseline_only_tickets": [ticket for ticket in baseline_top10 if ticket not in set(tickets)],
        }
    return {
        "model_id": MODEL,
        "race_key": key,
        "baseline_model_id": baseline.get("model_id"),
        "shadow_model_id": shadow.get("candidate_model_id"),
        "baseline_freeze_sha256": hashlib.sha256(canonical(baseline)).hexdigest(),
        "shadow_freeze_sha256": hashlib.sha256(canonical(shadow)).hexdigest(),
        "baseline_frozen_at_jst": baseline_time.isoformat(),
        "shadow_frozen_at_jst": shadow_time.isoformat(),
        "overlap_by_mode": overlaps,
        "same_race_predeadline_records": True,
        "source_authentication_verified": False,
        "github_first_seen_time_verified": False,
        "prediction_accuracy_evaluated": False,
        "performance_improvement_proven": False,
        "results_read": False,
        "formal_fresh_read": False,
        "model_promotion_authorized": False,
    }


def main():
    parser = argparse.ArgumentParser(description="Read-only pre-result Top10 comparison")
    parser.add_argument("--shadow", required=True, type=Path)
    parser.add_argument("--baseline", required=True, type=Path)
    args = parser.parse_args()
    shadow = json.loads(args.shadow.read_text(encoding="utf-8"))
    baseline = json.loads(args.baseline.read_text(encoding="utf-8"))
    print(json.dumps(compare(shadow, baseline), ensure_ascii=False, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
