#!/usr/bin/env python3
"""Read-only C-1 cohort accounting. Provisional readiness is NEVER a final miss.

Only V235's original first-Git-commit receipt can prove a successful save.
Observed races are not necessarily the independently eligible race denominator.
No result, payout, formal score, or prediction bytes are modified.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path

from boat_edge_v235_predeadline_receipt import JST, KEY, load, receipt

SCHEMA = "BOAT_EDGE_C1_OBSERVED_FIRST_GIT_ACCOUNTING_V1"


def parse_time(raw):
    try:
        value = datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
        return value if value.tzinfo is not None else None
    except (TypeError, ValueError, OverflowError):
        return None


def accounting(root: Path, now: datetime, audit_day: str | None = None) -> dict:
    if audit_day is not None and (len(audit_day) != 8 or not audit_day.isascii() or not audit_day.isdigit()):
        raise ValueError("audit_day must be YYYYMMDD")
    root = Path(root)
    now = now.astimezone(JST)
    day = (audit_day or now.strftime("%Y%m%d"))
    history = load(root / "data/site_paper_sim/readiness_history_v215" / (day + ".json"))
    observed = history.get("observations") or {}
    catalog = load(root / "data/today.json")
    same_day = (str(catalog.get("date") or "").replace("-", "") == day and
                now.strftime("%Y%m%d") == day)
    schedule = {}
    if same_day:
        for venue in catalog.get("venues") or []:
            for race in venue.get("races") or []:
                key = race.get("race_key")
                if isinstance(key, str) and KEY.fullmatch(key) and key.startswith(day + "-"):
                    schedule.setdefault(key, race.get("deadline"))
    rows = []
    for key, observation in sorted(observed.items()):
        if not isinstance(key, str) or not KEY.fullmatch(key) or not key.startswith(day + "-"):
            continue
        if not isinstance(observation, dict):
            continue
        # Historical observations retain the deadline after today.json rotates.
        # This is an observed clock, not independent eligibility proof.
        clock = schedule.get(key) or observation.get("deadline")
        deadline_source = "catalog" if key in schedule else "readiness_observation"
        if not isinstance(clock, str) or len(clock) != 5:
            rows.append({"race_key": key, "status": "UNKNOWN_DEADLINE",
                         "last_observed_reason": observation.get("reason")})
            continue
        try:
            due = datetime.strptime(day + clock, "%Y%m%d%H:%M").replace(tzinfo=JST)
        except ValueError:
            rows.append({"race_key": key, "status": "UNKNOWN_DEADLINE"})
            continue
        # The last recorded provisional 'snapshot_missing' must never be
        # classified as a failed final Git save merely because the clock passed.
        # Check the real Git first-add even if the readiness history is stale.
        proof = (receipt(root, now=now, requested=key, historical_deadline=clock)
                 if not same_day else receipt(root, now=now, requested=key))
        if proof.get("prediction_saved_proven") is True:
            status = "PROVEN_FIRST_GIT_BEFORE_DEADLINE"
        elif now < due:
            status = "PENDING_BEFORE_DEADLINE"
        else:
            status = "UNPROVEN_AFTER_DEADLINE"
        rows.append({"race_key": key, "status": status, "deadline": clock,
                     "receipt_status": proof.get("status"), "deadline_source": deadline_source,
                     "first_git_commit": proof.get("first_git_commit"),
                     "first_git_commit_at": proof.get("first_git_commit_at"),
                     "first_git_snapshot_sha256": proof.get("first_git_snapshot_sha256"),
                     "snapshot_sha256": proof.get("snapshot_sha256"),
                     "last_observed_reason": observation.get("reason"),
                     "last_observed_at": observation.get("last_seen_at"),
                     "source_gaps_at_last_observation": observation.get("source_gaps") or []})
    counts = dict(sorted(Counter(r["status"] for r in rows).items()))
    receipt_counts = dict(sorted(Counter(r.get("receipt_status") or "UNKNOWN" for r in rows).items()))
    gap_flags = dict(sorted(Counter(gap for r in rows for gap in r.get("source_gaps_at_last_observation", [])).items()))
    observation_reasons = dict(sorted(Counter(r.get("last_observed_reason") or "UNKNOWN" for r in rows).items()))
    missing_schedule = sorted(set(schedule) - {r["race_key"] for r in rows})
    return {"schema": SCHEMA, "day_jst": day, "checked_at_jst": now.isoformat(),
            "scope": "OBSERVED_ONLY_NOT_ELIGIBLE_DENOMINATOR",
            "official_result_files_read": False, "formal_prediction_files_read": False,
            "scheduled_races_catalog": len(schedule) if same_day else None,
            "observed_races": len(rows), "not_observed_count": len(missing_schedule),
            "classification_counts": counts, "receipt_status_counts": receipt_counts,
            "last_observation_source_gap_flags": gap_flags,
            "last_observation_reason_counts": observation_reasons,
            "source_gap_flags_are_not_root_causes": True, "races": rows,
            "c1_99_percent_proven": False,
            "eligible_denominator_verified": False,
            "interpretation": "Unproven after deadline is not proof of eligible missed freeze; pending is never a final failure."}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--now", default=None)
    parser.add_argument("--day", default=None, help="Observed race day YYYYMMDD; no historical backfill")
    args = parser.parse_args()
    now = parse_time(args.now) if args.now else datetime.now(timezone.utc)
    if now is None:
        parser.error("invalid timezone-aware --now")
    print(json.dumps(accounting(Path(args.root), now, args.day), ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
