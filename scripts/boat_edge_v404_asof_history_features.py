#!/usr/bin/env python3
"""V404: time-safe historical feature snapshot, never a production prediction.

Only reads operator-staged, rights-reviewed V400 history and a synthetic or
operator-staged *pre-race B-only* target roster. It uses each historical
result only when its independently-unverified recorded published_at is strictly
before the target deadline. It DOES NOT authenticate that timestamp.
Never read target finish/actual course or score Formal Fresh outcomes.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path

from boat_edge_v400_five_year_history_research import (
    FIVE_YEAR_START, FIVE_YEAR_END_EXCLUSIVE, JST, WINDOWS,
    _jst_instant, iter_races, validate_manifest,
)

MODEL = "BOAT_EDGE_V404_ASOF_HISTORY_FEATURES_RESEARCH_V1"
TARGET_SCHEMA = "BOAT_EDGE_V404_B_ONLY_TARGET_ROSTER_V1"
BOATS = set(range(1, 7))
RACE_KEY = re.compile(r"[0-9]{12}\Z")
RACER_ID = re.compile(r"[0-9]{4}\Z")
METRICS = ("entries", "first", "second", "third")
# A W-day calendar window includes age 0 .. W-1 (exactly W dates).
# With age 0, only independently time-stamped earlier same-day K results qualify.


def _target(target):
    if not isinstance(target, dict) or set(target) != {
        "schema", "race_key", "deadline_jst", "entries"
    } or target.get("schema") != TARGET_SCHEMA:
        raise ValueError("EXACT_B_ONLY_TARGET_REQUIRED")
    key = target["race_key"]
    if not isinstance(key, str) or RACE_KEY.fullmatch(key) is None:
        raise ValueError("INVALID_TARGET_RACE_KEY")
    try:
        day = date.fromisoformat(f"{key[:4]}-{key[4:6]}-{key[6:8]}")
        venue, race_no = int(key[8:10]), int(key[10:12])
    except ValueError as exc:
        raise ValueError("INVALID_TARGET_DATE") from exc
    if not (FIVE_YEAR_START <= day < FIVE_YEAR_END_EXCLUSIVE and
            1 <= venue <= 24 and 1 <= race_no <= 12):
        raise ValueError("PROTECTED_OR_UNSUPPORTED_TARGET_DATE")
    deadline = _jst_instant(target["deadline_jst"])
    if deadline.date() != day:
        raise ValueError("TARGET_DEADLINE_DATE_MISMATCH")
    entries = target["entries"]
    if not isinstance(entries, list) or len(entries) != 6:
        raise ValueError("SIX_B_ONLY_TARGET_ENTRIES_REQUIRED")
    racers = {}
    for entry in entries:
        if not isinstance(entry, dict) or set(entry) != {"boat", "racer_id"}:
            raise ValueError("TARGET_MUST_NOT_CONTAIN_OUTCOME_OR_ACTUAL_COURSE")
        boat, racer = entry["boat"], entry["racer_id"]
        if (type(boat) is not int or boat not in BOATS or boat in racers
                or not isinstance(racer, str) or RACER_ID.fullmatch(racer) is None):
            raise ValueError("INVALID_TARGET_BOAT_OR_RACER")
        racers[boat] = racer
    if set(racers) != BOATS or len(set(racers.values())) != 6:
        raise ValueError("TARGET_REQUIRES_SIX_DISTINCT_RACERS")
    return key, deadline, venue, racers


def _new_counter():
    return [0, 0, 0, 0]


def _bump(counter, finish):
    counter[0] += 1
    if finish <= 3:
        counter[finish] += 1


def _emit(counts):
    return {str(w): dict(zip(METRICS, counts.get(w, _new_counter())))
            for w in WINDOWS}


def snapshot(raw: bytes, manifest: dict, target: dict):
    key, deadline, venue, racers = _target(target)
    if not isinstance(raw, bytes):
        raise ValueError("HISTORY_CSV_BYTES_REQUIRED")
    if not isinstance(manifest, dict):
        raise ValueError("HISTORY_SOURCE_MANIFEST_REQUIRED")
    # The historic model freeze remains a *separate* 2026-10-01 cutoff.
    # This check prevents a manifest from authorizing anything after Formal Fresh lock.
    validate_manifest(manifest, raw, datetime.combine(
        FIVE_YEAR_END_EXCLUSIVE, datetime.min.time(), JST))
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeError as exc:
        raise ValueError("HISTORY_UTF8_REQUIRED") from exc

    all_counts = defaultdict(dict)
    venue_counts = defaultdict(dict)
    racer_counts = defaultdict(dict)
    seen_before = 0
    seen_late = 0
    same_target = 0
    first_history = None
    last_history = None
    for rows in iter_races(text, datetime.combine(
        FIVE_YEAR_END_EXCLUSIVE, datetime.min.time(), JST)):
        item = rows[0]
        history_key, history_day, history_venue, published = (
            item[0], item[1], item[2], item[7])
        if history_key == key:
            # Exclude target outcomes even if bogus source timestamps suggest
            # they preceded race close; this is a retrospective safety fence.
            same_target += 1
            continue
        if not published < deadline:
            seen_late += 1
            continue
        age = (deadline.date() - history_day).days
        if age < 0 or age >= max(WINDOWS):
            continue
        seen_before += 1
        first_history = min(first_history, history_day) if first_history else history_day
        last_history = max(last_history, history_day) if last_history else history_day
        for row in rows:
            _, _, _, _, racer, course, finish, _ = row
            for w in WINDOWS:
                if age < w:
                    for store, group in (
                        (all_counts, "all"),
                        (venue_counts, history_venue),
                        (racer_counts, racer),
                    ):
                        if store is racer_counts and racer not in racers.values():
                            continue
                        if store is venue_counts and history_venue != venue:
                            continue
                        key2 = (group, course)
                        if w not in store[key2]:
                            store[key2][w] = _new_counter()
                        _bump(store[key2][w], finish)

    def group_counts(store, name):
        return {str(course): _emit(store.get((name, course), {}))
                for course in range(1, 7)}

    return {
        "schema": MODEL, "research_only": True,
        "target": {"race_key": key, "deadline_jst": deadline.isoformat(),
                   "venue": f"{venue:02d}", "boat_racer_ids":
                   {str(b): racers[b] for b in sorted(racers)}},
        "source_sha256": hashlib.sha256(raw).hexdigest(),
        "historic_publication_timestamps_independently_verified": False,
        "historic_source_rights_independently_verified": False,
        "target_b_roster_historic_predeadline_capture_verified": False,
        "results_downloaded": False, "formal_fresh_read": False,
        "retrospective_features_only": True,
        "historical_races_eligible_before_target": seen_before,
        "historical_races_not_yet_available": seen_late,
        "same_target_outcome_excluded": same_target,
        "history_min_date": first_history.isoformat() if first_history else None,
        "history_max_date": last_history.isoformat() if last_history else None,
        "rolling_windows_days": list(WINDOWS),
        "national_actual_course_counts": group_counts(all_counts, "all"),
        "venue_actual_course_counts": group_counts(venue_counts, venue),
        "racer_actual_course_counts_by_boat": {
            str(boat): {"racer_id": racers[boat],
                         "course_counts": group_counts(racer_counts, racers[boat])}
            for boat in sorted(racers)
        },
        "actual_course_of_target_not_observed_or_inferred": True,
        "calibrated": False, "accuracy_improvement_proven": False,
        "production_model_changed": False, "model_promotion_authorized": False,
        "wagers_authorized": False,
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--history-csv", type=Path, required=True)
    p.add_argument("--history-manifest", type=Path, required=True)
    p.add_argument("--b-only-target", type=Path, required=True)
    args = p.parse_args()
    result = snapshot(
        args.history_csv.read_bytes(),
        json.loads(args.history_manifest.read_text(encoding="utf-8")),
        json.loads(args.b_only_target.read_text(encoding="utf-8")),
    )
    print(json.dumps(result, sort_keys=True, ensure_ascii=False, separators=(",", ":")))


if __name__ == "__main__":
    main()
