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
import hashlib
import re
import json
from pathlib import Path

from boat_edge_v235_predeadline_receipt import JST, KEY, load, receipt, git, instant

SCHEMA = "BOAT_EDGE_C1_OBSERVED_FIRST_GIT_ACCOUNTING_V1"


def parse_time(raw):
    try:
        value = datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
        return value if value.tzinfo is not None else None
    except (TypeError, ValueError, OverflowError):
        return None


def archived_receipt(root: Path, key: str, due: datetime) -> dict:
    """Independent historical first-Git evidence; never upgrades eligibility.

    Uses only original committed snapshot bytes, committed time, V229 audit,
    and pre-result snapshot metadata. Does not read scores or results.
    """
    rel = "data/site_prediction_snapshots/" + key + ".json"
    path = root / rel
    if not path.is_file():
        return {"prediction_saved_proven": False, "status": "ARCHIVE_NO_SNAPSHOT"}
    raw = path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    snap = load(path)
    audit = load(root / "data/site_prediction_audit" / (key + ".json"))
    evidence = load(root / "data/site_autopilot/v229_evidence" / (key + ".json"))
    saved = instant(snap.get("first_saved_at"))
    if (snap.get("race_key") != key or snap.get("snapshot_window") != "FINAL_15M"
            or snap.get("prediction_kind") != "SITE_REFERENCE_V122"
            or any((snap.get("guards") or {}).get(x) is not False
                   for x in ("results_seen", "unlock", "scoring"))
            or audit.get("pass") is not True
            or audit.get("latest_snapshot_sha256") != digest
            or evidence.get("snapshot_sha256") != digest
            or evidence.get("race_key") != key
            or evidence.get("new_snapshot_created_this_run") is not True
            or saved is None
            or not 2 <= (due - saved).total_seconds() / 60 <= 10):
        return {"prediction_saved_proven": False, "status": "ARCHIVE_SOURCE_OR_TIME_UNVERIFIED"}
    commits = git(root, "log", "--diff-filter=A", "--format=%H", "--", rel)
    if not commits:
        return {"prediction_saved_proven": False, "status": "ARCHIVE_NO_FIRST_GIT_ADD"}
    sha = commits.decode("utf-8", "replace").strip().splitlines()[-1]
    if not re.fullmatch(r"[0-9a-f]{40}", sha):
        return {"prediction_saved_proven": False, "status": "ARCHIVE_BAD_COMMIT_SHA"}
    original = git(root, "show", sha + ":" + rel)
    committed = git(root, "show", "-s", "--format=%cI", sha)
    commit_time = instant(committed.decode().strip()) if committed else None
    if (original is None or hashlib.sha256(original).hexdigest() != digest
            or commit_time is None or commit_time >= due):
        return {"prediction_saved_proven": False, "status": "ARCHIVE_FIRST_GIT_PROOF_UNVERIFIED"}
    return {"prediction_saved_proven": True, "status": "ARCHIVED_FIRST_GIT_PREDEADLINE",
            "first_git_commit": sha, "first_git_commit_at": commit_time.isoformat()}


def accounting(root: Path, now: datetime, day: str | None = None) -> dict:
    root = Path(root)
    now = now.astimezone(JST)
    day = day or now.strftime("%Y%m%d")
    if not re.fullmatch(r"20\d{6}", day):
        raise ValueError("day must be YYYYMMDD")
    history = load(root / "data/site_paper_sim/readiness_history_v215" / (day + ".json"))
    observed = history.get("observations") or {}
    catalog = load(root / "data/today.json")
    # A stale today.json can still point at yesterday after JST rollover.
    # V235 receipt requires its race day to equal the *actual* current JST day.
    catalog_matches_day = str(catalog.get("date") or "").replace("-", "") == day
    same_day = catalog_matches_day and day == now.strftime("%Y%m%d")
    schedule = {}
    # Retain historical catalog coverage when yesterday's card remains cached.
    if catalog_matches_day:
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
        clock = schedule.get(key)
        if not same_day:
            # Historic catalog is overwritten on rollover; history keeps
            # the observed deadline but is not an eligibility certificate.
            clock = observation.get("deadline")
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
        proof = (receipt(root, now=now, requested=key) if same_day
                 else archived_receipt(root, key, due))
        if proof.get("prediction_saved_proven") is True:
            status = "PROVEN_FIRST_GIT_BEFORE_DEADLINE"
        elif now < due:
            status = "PENDING_BEFORE_DEADLINE"
        else:
            status = "UNPROVEN_AFTER_DEADLINE"
        rows.append({"race_key": key, "status": status, "deadline": clock,
                     "receipt_status": proof.get("status"),
                     "last_observed_reason": observation.get("reason"),
                     "last_observed_at": observation.get("last_seen_at"),
                     "source_gaps_at_last_observation": observation.get("source_gaps") or []})
    counts = dict(sorted(Counter(r["status"] for r in rows).items()))
    missing_schedule = sorted(set(schedule) - {r["race_key"] for r in rows})
    return {"schema": SCHEMA, "day_jst": day, "checked_at_jst": now.isoformat(),
            "scope": "OBSERVED_ONLY_NOT_ELIGIBLE_DENOMINATOR",
            "deadline_source": "CURRENT_DAY_CATALOG" if same_day else "HISTORICAL_V215_OBSERVATION_UNVERIFIED",
            "official_result_files_read": False, "formal_prediction_files_read": False,
            "scheduled_races_catalog": len(schedule) if catalog_matches_day else None,
            "historical_catalog_is_stale": catalog_matches_day and not same_day,
            "observed_races": len(rows),
            "not_observed_count": len(missing_schedule) if catalog_matches_day else None,
            "classification_counts": counts, "races": rows,
            "c1_99_percent_proven": False,
            "eligible_denominator_verified": False,
            "interpretation": "Unproven after deadline is not proof of eligible missed freeze; pending is never a final failure."}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--now", default=None)
    parser.add_argument("--day", default=None, help="YYYYMMDD observation cohort, including previous days")
    args = parser.parse_args()
    now = parse_time(args.now) if args.now else datetime.now(timezone.utc)
    if now is None:
        parser.error("invalid timezone-aware --now")
    print(json.dumps(accounting(Path(args.root), now, day=args.day), ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
