#!/usr/bin/env python3
"""V331 diagnose PRE_RESULT inputs for a future live freeze, without freezing.

One pass over a race card to show exact missing prerequisites, even when the
race deadline is already closed. Closed races remain NOT eligible for freezing.
No results, formal data, payouts, odds, network, or writes.
"""
from __future__ import annotations

import argparse
from datetime import datetime
import json
from pathlib import Path

from boat_edge_v312_pre_result_ablation import build_shadow
from boat_edge_v316_receipt_assemble import assemble
from boat_edge_v318_shadow_freeze import JST, KEY, parse_time


def diagnose(root, race_key, now=None):
    if not isinstance(race_key, str) or KEY.fullmatch(race_key) is None:
        raise ValueError("INVALID_RACE_KEY")
    root = root.resolve()
    now = now if now is not None else datetime.now(JST)
    if now.tzinfo is None or now.utcoffset() is None:
        raise ValueError("AWARE_CLOCK_REQUIRED")
    now = now.astimezone(JST)
    path = root / "data/races" / (race_key + ".json")
    if path.is_symlink():
        raise ValueError("RACE_SYMLINK_FORBIDDEN")
    race = json.loads(path.read_text(encoding="utf-8"))
    meta = race.get("meta")
    if not isinstance(meta, dict) or race.get("race_key") != race_key:
        raise ValueError("INVALID_RACE")
    if meta.get("phase") != "PRE_RESULT" or any(meta.get(k) is not False for k in ("results_seen", "unlock", "scoring")):
        raise ValueError("RESULT_OR_UNLOCK_FORBIDDEN")
    if meta.get("date", "").replace("-", "") != race_key[:8]:
        raise ValueError("RACE_DATE_MISMATCH")
    deadline = parse_time(meta["date"] + "T" + meta["deadline"] + ":00+09:00")
    issues = []
    if now >= deadline:
        issues.append("DEADLINE_CLOSED_NO_RETROACTIVE_FREEZE")
    for label, raw in [("race_updated", meta.get("updated_at"))] + [
        (name, (race.get("source_audit") or {}).get(name, {}).get("fetched_at"))
        for name in ("race_card", "beforeinfo")
    ]:
        try:
            stamp = datetime.fromisoformat(raw)
            if stamp.tzinfo is None or stamp.utcoffset() is None:
                raise ValueError("naive")
            if stamp >= deadline:
                issues.append("POSTDEADLINE_" + label)
            if stamp > now:
                issues.append("FUTURE_TIMESTAMP_" + label)
        except (ValueError, TypeError):
            issues.append("INVALID_TIMESTAMP_" + label)
    try:
        candidate = build_shadow(race)
        candidate_ready = True
        candidate_error = None
    except (ValueError, KeyError, TypeError) as exc:
        candidate_ready = False
        candidate_error = str(exc)
        issues.append("CANDIDATE_NOT_READY")
    report = assemble(root, race_key, deadline.isoformat())
    receipt_ready = report["ready_for_research_review"]
    if not receipt_ready:
        issues.append("THREE_SOURCE_RECEIPTS_NOT_READY")
    return {
        "race_key": race_key, "deadline_jst": deadline.isoformat(),
        "candidate_ready": candidate_ready, "candidate_error": candidate_error,
        "three_source_receipts_ready": receipt_ready,
        "missing_or_invalid_receipts": report["missing_or_invalid_receipts"],
        "ready_for_live_freeze": not issues, "issues": issues,
        "candidate_modes": sorted(candidate["modes"]) if candidate_ready else [],
        "results_read": False, "formal_fresh_read": False, "writes_performed": False,
        "accuracy_improvement_proven": False,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--race-key", required=True)
    args = parser.parse_args()
    print(json.dumps(diagnose(args.root, args.race_key), ensure_ascii=False, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
