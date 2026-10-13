#!/usr/bin/env python3
"""V365: read-only source-refresh candidate contract for Track 01 integration.

Unlike V230.targets(), this selector does not discard an open PRE_RESULT race
merely because its independent first site prediction is already frozen. It
NEVER fetches, writes, freezes, authorizes prediction, reads results, or opens
site prediction snapshots. Track 01 must independently review any integration.
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
import re

from boat_edge_v230_fast_lane import due_for, load, JST

MODEL = "BOAT_EDGE_V365_SOURCE_REFRESH_SELECTION_CONTRACT_ONLY"
KEY = re.compile(r"^20\d{6}-(?:0[1-9]|1\d|2[0-4])-(?:0[1-9]|1[0-2])$")
RESULT_KEYS = frozenset(("results", "result", "payout", "finish", "outcomes"))
LOCK_KEYS = ("results_seen", "unlock", "scoring")


def select_source_refresh(root, now, max_target=12):
    """Conservative 2–19 min candidate scan, independent of first-pick state."""
    if not isinstance(now, datetime) or now.tzinfo is None or now.utcoffset() is None:
        raise ValueError("V365_AWARE_CLOCK_REQUIRED")
    if type(max_target) is not int or not 1 <= max_target <= 12:
        raise ValueError("V365_INVALID_CAP")
    now = now.astimezone(JST)
    root = Path(root).resolve()
    today = now.strftime("%Y%m%d")
    today_path = root / "data/today.json"
    if today_path.is_symlink():
        raise ValueError("V365_TODAY_SYMLINK_FORBIDDEN")
    index = load(today_path)
    if not isinstance(index, dict) or str(index.get("date", "")).replace("-", "") != today:
        return {
            "model_id": MODEL, "day_jst": today, "candidates": [],
            "rejected": {"INDEX_NOT_CURRENT_OR_VALID": 1},
            "source_refresh_performed": False, "first_prediction_opened": False,
            "results_read": False, "formal_fresh_read": False,
            "writes_performed": False, "production_prediction_changed": False,
        }
    venues = index.get("venues")
    if not isinstance(venues, list):
        raise ValueError("V365_INVALID_VENUES")
    pool, rejected, seen = [], {}, set()

    def reject(reason):
        rejected[reason] = rejected.get(reason, 0) + 1

    for venue in venues:
        if not isinstance(venue, dict) or not isinstance(venue.get("races"), list):
            reject("VENUE_OR_RACES_NOT_VALID")
            continue
        jcd = str(venue.get("jcd", "")).zfill(2)
        if not re.fullmatch(r"(?:0[1-9]|1\d|2[0-4])", jcd):
            reject("VENUE_ID_INVALID")
            continue
        for row in venue["races"]:
            if not isinstance(row, dict):
                reject("INDEX_ROW_INVALID")
                continue
            key = row.get("race_key")
            if not isinstance(key, str) or KEY.fullmatch(key) is None or key[:8] != today:
                reject("INVALID_RACE_KEY")
                continue
            if key in seen:
                reject("DUPLICATE_INDEX_RACE")
                pool = [item for item in pool if item[1] != key]
                continue
            seen.add(key)
            if key[9:11] != jcd:
                reject("VENUE_MISMATCH")
                continue
            deadline = due_for(key, row.get("deadline"))
            if deadline is None:
                reject("INDEX_DEADLINE_INVALID")
                continue
            minutes = (deadline - now).total_seconds() / 60
            if not 2 <= minutes <= 19:
                reject("OUTSIDE_LIVE_2_TO_19_MINUTES")
                continue
            race_path = root / "data/races" / (key + ".json")
            if race_path.is_symlink():
                reject("RACE_SYMLINK_FORBIDDEN")
                continue
            race = load(race_path)
            if not isinstance(race, dict):
                reject("RACE_DOCUMENT_INVALID_OR_MISSING")
                continue
            meta = race.get("meta")
            if (not isinstance(meta, dict) or race.get("race_key") != key
                    or meta.get("phase") != "PRE_RESULT"
                    or any(meta.get(flag) is not False for flag in LOCK_KEYS)
                    or RESULT_KEYS.intersection(race)
                    or str(meta.get("date", "")).replace("-", "") != today
                    or meta.get("deadline") != row.get("deadline")
                    or str(meta.get("venue_code", "")).zfill(2) != jcd
                    or type(meta.get("race_no")) is not int
                    or meta.get("race_no") != int(key[-2:])):
                reject("RACE_IDENTITY_OR_PRE_RESULT_GUARD_INVALID")
                continue
            racers = race.get("racers")
            if not isinstance(racers, list) or len(racers) != 6:
                reject("SIX_RACE_ENTRIES_REQUIRED")
                continue
            snapshot = root / "data/site_prediction_snapshots" / (key + ".json")
            # The file is deliberately not read, parsed or hashed.
            if snapshot.is_symlink():
                reject("FIRST_PREDICTION_SYMLINK")
                continue
            pool.append((deadline, key, {
                "race_key": key, "minutes_until_deadline": round(minutes, 3),
                "independent_site_first_prediction_exists": snapshot.is_file(),
                "refresh_only_no_first_prediction_overwrite": True,
                "source_fetch_permitted_by_this_scan": False,
            }))
    pool.sort(key=lambda item: (item[0], item[1]))
    return {
        "model_id": MODEL, "day_jst": today,
        "candidates": [x[2] for x in pool[:max_target]],
        "deferred_due_to_cap": [x[1] for x in pool[max_target:]],
        "rejected": dict(sorted(rejected.items())),
        "source_refresh_performed": False,
        "first_prediction_opened": False,
        "results_read": False,
        "formal_fresh_read": False,
        "writes_performed": False,
        "production_prediction_changed": False,
        "formal_unlock_authorized": False,
        "can_authorize_prediction_or_capture": False,
    }
