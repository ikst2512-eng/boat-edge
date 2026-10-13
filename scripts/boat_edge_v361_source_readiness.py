#!/usr/bin/env python3
"""V361: read-only SITE pre-result input readiness diagnostics at selection time.

Purely descriptive and sampled from already-read raw race-card bytes. NEVER
make a candidate eligible, infer a course, authenticate sources, or touch
outcomes. Use only for current-day predeadline cards with all Formal locks off.
"""
from __future__ import annotations

from datetime import datetime
import hashlib
import math
import re

from boat_edge_v311_existing_source_audit import audit_race
from boat_edge_v318_shadow_freeze import JST

REQUIRED = set(range(1, 7))
STALE_LIMITS_SECONDS = {"race_card": 16 * 60, "beforeinfo": 15 * 60}


def _age_in_seconds(iso, now):
    if not isinstance(iso, str):
        return None
    try:
        stamp = datetime.fromisoformat(iso)
    except (TypeError, ValueError):
        return None
    if stamp.tzinfo is None or stamp.utcoffset() is None:
        return None
    return round((now - stamp.astimezone(JST)).total_seconds(), 3)


def _good(value, lower, upper):
    return type(value) in (int, float) and math.isfinite(value) and lower <= value <= upper


def scan_preflight(race, raw, now):
    """A snapshot from the selection-time read, NOT an authenticated freeze input."""
    if type(raw) is not bytes or not isinstance(race, dict) or not isinstance(now, datetime):
        raise ValueError("SCAN_INPUT_INVALID")
    if now.tzinfo is None or now.utcoffset() is None:
        raise ValueError("SCAN_AWARE_CLOCK_REQUIRED")
    now = now.astimezone(JST)
    key, meta = race.get("race_key"), race.get("meta")
    if (not isinstance(key, str) or not re.fullmatch(r"20\d{6}-(?:0[1-9]|1\d|2[0-4])-(?:0[1-9]|1[0-2])", key)
            or not isinstance(meta, dict) or meta.get("phase") != "PRE_RESULT"
            or any(meta.get(k) is not False for k in ("results_seen", "unlock", "scoring"))
            or now.strftime("%Y%m%d") != key[:8]
            or any(k in race for k in ("results", "result", "payout", "finish", "outcomes"))):
        raise ValueError("SCAN_PRE_RESULT_ONLY")
    report = audit_race(race)
    if now >= datetime.fromisoformat(report["deadline_jst"]):
        raise ValueError("SCAN_CLOSED_RACE")
    issues = [
        reason for reason in report["reasons"]
        if reason in ("RACE_CARD_NOT_PREDEADLINE_PROVEN", "BEFOREINFO_NOT_PREDEADLINE_PROVEN",
                      "START_EXHIBITION_COURSE_MISSING_OR_INVALID")
    ]
    statuses, ages = {}, {}
    source = race.get("source_audit") if isinstance(race.get("source_audit"), dict) else {}
    for name, limit in STALE_LIMITS_SECONDS.items():
        entry = source.get(name)
        entry = entry if isinstance(entry, dict) else {}
        statuses[name] = entry.get("status") if isinstance(entry.get("status"), str) else None
        age = _age_in_seconds(entry.get("fetched_at"), now)
        ages[name] = age
        if statuses[name] != "ok":
            issues.append("SOURCE_NOT_OK:" + name)
        if age is None:
            issues.append("SOURCE_SCAN_TIMESTAMP_UNKNOWN:" + name)
        elif age < 0:
            issues.append("SOURCE_SCAN_TIMESTAMP_FUTURE:" + name)
        elif age > limit:
            issues.append("SOURCE_SCAN_STALE:" + name)
    starts = (race.get("beforeinfo") or {}).get("start_exhibition") if isinstance(race.get("beforeinfo"), dict) else []
    starts = starts if isinstance(starts, list) else []
    explicit_courses = sorted({
        row["lane"] for row in starts if isinstance(row, dict)
        and type(row.get("lane")) is int and row["lane"] in REQUIRED
        and type(row.get("course")) is int and row["course"] in REQUIRED
    })
    racers = race.get("racers")
    racers = racers if isinstance(racers, list) else []
    feature_boats = set()
    for row in racers:
        if not isinstance(row, dict):
            continue
        boat = row.get("lane")
        national = row.get("national")
        motor = row.get("motor")
        if (type(boat) is int and boat in REQUIRED and isinstance(national, dict)
                and isinstance(motor, dict)
                and _good(national.get("win_rate"), .01, 10)
                and _good(motor.get("quinella_rate"), 0, 100)
                and _good(row.get("avg_st"), .01, 1)):
            feature_boats.add(boat)
    if feature_boats != REQUIRED or len(racers) != 6:
        issues.append("SIX_RACER_FEATURES_INCOMPLETE")
    result = {
        "model_id": "BOAT_EDGE_V361_SITE_SELECTION_INPUT_DIAGNOSTIC_ONLY",
        "race_key": key,
        "selection_sampled_at_jst": now.isoformat(),
        "selection_race_input_sha256": hashlib.sha256(raw).hexdigest(),
        "reported_source_statuses": statuses,
        "reported_source_age_seconds_at_selection": ages,
        "start_exhibition_explicit_course_lanes": explicit_courses,
        "start_exhibition_provisional_permutation_recorded": report["start_exhibition_course_permutation_recorded"],
        "feature_complete_boats": sorted(feature_boats),
        "issues": sorted(set(issues)),
        "preflight_can_authorize_freeze": False,
        "selection_snapshot_may_differ_from_freeze_input": True,
        "source_bytes_independently_authenticated": False,
        "actual_entry_independently_verified": False,
        "results_read": False,
        "formal_fresh_read": False,
        "accuracy_improvement_proven": False,
        "model_promotion_authorized": False,
        "writes_performed": False,
    }
    return result
