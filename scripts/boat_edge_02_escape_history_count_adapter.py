"""Track 02 — authorized historic COURSE-1 NIGE cohort count adapter.

Offline, no filesystem/network/outcome collector. This accepts ONLY explicitly
rights-reviewed, independently time-pinned historical event records, NOT current
Formal Fresh results. It emits input counts for the existing isolated
boat_edge_02_escape_second_third_research estimator; no fresh prediction,
calibration, betting, production code or target-result access is performed.

The rights, historical first-publication clock and manifest SHA are assertions
by the caller, NOT independently authenticated by this function.
"""
from __future__ import annotations

from datetime import date, datetime, timezone, timedelta
import hashlib
import json
import re

from boat_edge_02_hierarchical_conditional_research import _check_scope

MODEL = "BOAT_EDGE_02_AUTHORIZED_HISTORICAL_ESCAPE_COHORT_V1"
JST = timezone(timedelta(hours=9))
LANES = frozenset(range(1, 7))
TAIL = frozenset(range(2, 7))
LAYERS = ("national", "venue", "racer", "motor")
DATE_KEY = re.compile(r"20\d{6}-(?:0[1-9]|1\d|2[0-4])-(?:0[1-9]|1[0-2])\Z")
HEX = re.compile(r"[0-9a-f]{64}\Z")
# Dates already associated with protected formal cohorts. This hard deny-list
# must not substitute for the dynamically provided current formal target.
KNOWN_PROTECTED = frozenset(("20261001", "20261005", "20261013"))
CONTEXT = {
    "schema", "scope", "race_key", "target_venue", "target_c1_racer",
    "target_c1_motor_epoch", "locked_formal_dates",
    "rights_reviewed_for_historical_training",
    "historical_raw_manifest_sha256", "permission_evidence_sha256",
    "training_data_first_git_commit_sha", "training_data_first_git_server_time_jst",
    "all_events_are_c1_nige_with_official_final_course",
}
ROW = {
    "race_key", "venue", "official_kimarite", "source_kind",
    "final_actual_course_to_boat", "official_full_finish_boats",
    "racer_id_by_boat", "motor_epoch_by_boat",
    "result_first_available_at_jst", "source_raw_sha256",
}


def _when(value):
    if not isinstance(value, str):
        raise ValueError("INVALID_PUBLICATION_TIME")
    try:
        dt = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError("INVALID_PUBLICATION_TIME") from exc
    if dt.tzinfo is None or dt.utcoffset() != timedelta(hours=9):
        raise ValueError("PUBLICATION_MUST_HAVE_JST_OFFSET")
    return dt


def _assert_digest(value, label):
    if not isinstance(value, str) or not HEX.fullmatch(value):
        raise ValueError("INVALID_" + label)


def _event_date(key):
    if not isinstance(key, str) or DATE_KEY.fullmatch(key) is None:
        raise ValueError("BAD_HISTORICAL_RACE_KEY")
    try:
        return date(int(key[:4]), int(key[4:6]), int(key[6:8]))
    except ValueError as exc:
        raise ValueError("BAD_HISTORICAL_RACE_KEY") from exc


def _target_context(scope, target):
    if not isinstance(target, dict) or set(target) != CONTEXT:
        raise ValueError("EXACT_TRAINING_TARGET_CONTEXT_REQUIRED")
    key = target["race_key"]
    _check_scope(scope, key)
    if target["schema"] != "BE02_HISTORICAL_ESCAPE_TRAINING_CONTEXT_V1" or target["scope"] != "RESEARCH_ONLY_PRE_RESULT":
        raise ValueError("RESEARCH_CONTEXT_REQUIRED")
    if target["rights_reviewed_for_historical_training"] is not True or (
            target["all_events_are_c1_nige_with_official_final_course"] is not True):
        raise ValueError("HISTORICAL_RIGHTS_AND_SEMANTICS_REQUIRED")
    if not isinstance(target["target_venue"], int) or type(target["target_venue"]) is not int or (
            not 1 <= target["target_venue"] <= 24):
        raise ValueError("BAD_TARGET_VENUE")
    if int(key.split("-")[1]) != target["target_venue"]:
        raise ValueError("TARGET_VENUE_AND_RACE_KEY_MISMATCH")
    for name in ("target_c1_racer", "target_c1_motor_epoch"):
        if target[name] is not None and (
                not isinstance(target[name], str) or not target[name] or len(target[name]) > 64):
            raise ValueError("INVALID_TARGET_IDENTIFIER:" + name)
    if target["target_c1_motor_epoch"] is not None and target["target_c1_racer"] is None:
        raise ValueError("MOTOR_LAYER_REQUIRES_RACER")
    for k in ("historical_raw_manifest_sha256", "permission_evidence_sha256"):
        _assert_digest(target[k], k.upper())
    if target["permission_evidence_sha256"] != scope["reviewed_permission_evidence_sha256"]:
        raise ValueError("PERMISSION_PROVENANCE_MISMATCH")
    if target["historical_raw_manifest_sha256"] != scope["source_manifest_sha256"]:
        raise ValueError("HISTORICAL_MANIFEST_MISMATCH")
    if not isinstance(target["training_data_first_git_commit_sha"], str) or not re.fullmatch(
            r"[0-9a-f]{40}", target["training_data_first_git_commit_sha"]):
        raise ValueError("FIRST_GIT_COMMIT_SHA_REQUIRED")
    frozen = _when(scope["first_frozen_at"])
    first_git = _when(target["training_data_first_git_server_time_jst"])
    if not first_git < frozen:
        raise ValueError("TRAINING_NOT_PUBLISHED_BEFORE_FREEZE")
    dates = target["locked_formal_dates"]
    if not isinstance(dates, list) or not dates or not all(
            isinstance(d, str) and re.fullmatch(r"20\d{6}", d) for d in dates):
        raise ValueError("EXPLICIT_CURRENT_FORMAL_DATE_BLOCKLIST_REQUIRED")
    if len(set(dates)) != len(dates) or target["race_key"][:8] in dates:
        raise ValueError("LOCKED_FORMAL_TARGET_REFUSED")
    return frozen, set(dates) | KNOWN_PROTECTED


def _empty():
    second = {course: 0 for course in sorted(TAIL)}
    third = {s: {t: 0 for t in sorted(TAIL - {s})} for s in sorted(TAIL)}
    return second, third


def _event(row, cutoff, frozen, blocked):
    if not isinstance(row, dict) or set(row) != ROW:
        raise ValueError("EXACT_HISTORICAL_ROW_SCHEMA_REQUIRED")
    key = row["race_key"]
    race_day = _event_date(key)
    if key[:8] in blocked:
        raise ValueError("PROTECTED_FORMAL_HISTORICAL_EVENT_REJECTED")
    if race_day > cutoff:
        raise ValueError("HISTORICAL_EVENT_AFTER_TRAINING_CUTOFF")
    observed = _when(row["result_first_available_at_jst"])
    # The raw file could have been published after its race day; only events
    # independently available before the candidate freeze can be considered.
    if observed.date() < race_day or observed >= frozen:
        raise ValueError("HISTORICAL_EVENT_NOT_AVAILABLE_PRE_FREEZE")
    _assert_digest(row["source_raw_sha256"], "HISTORICAL_SOURCE")
    if (row["source_kind"] != "OFFICIAL_AUTHORIZED_HISTORICAL_FINISH_KIMARITE_AND_ACTUAL_ENTRY"
            or row["official_kimarite"] != "nige"):
        raise ValueError("NOT_OFFICIALLY_VERIFIED_COURSE_ONE_NIGE")
    if type(row["venue"]) is not int or not 1 <= row["venue"] <= 24 or (
            int(key.split("-")[1]) != row["venue"]):
        raise ValueError("BAD_HISTORICAL_VENUE")
    actual = row["final_actual_course_to_boat"]
    order = row["official_full_finish_boats"]
    if (not isinstance(actual, dict) or set(actual) != LANES or
            any(type(b) is not int for b in actual.values()) or
            set(actual.values()) != LANES):
        raise ValueError("HISTORICAL_ACTUAL_ENTRY_NOT_SIX_PERMUTATION")
    if (not isinstance(order, list) or len(order) != 6 or
            any(type(b) is not int for b in order) or set(order) != LANES):
        raise ValueError("HISTORICAL_FINISH_NOT_SIX_PERMUTATION")
    if order[0] != actual[1]:
        raise ValueError("NIGE_WINNER_NOT_CONFIRMED_ACTUAL_COURSE_ONE")
    inverse = {boat: course for course, boat in actual.items()}
    second, third = inverse[order[1]], inverse[order[2]]
    if second not in TAIL or third not in (TAIL - {second}):
        raise ValueError("NOT_TWO_DISTINCT_TAIL_COURSES")
    racers = row["racer_id_by_boat"]
    motors = row["motor_epoch_by_boat"]
    if (not isinstance(racers, dict) or set(racers) != LANES or
            not isinstance(motors, dict) or set(motors) != LANES):
        raise ValueError("SIX_IDENTITIES_REQUIRED")
    if any(not isinstance(v, str) or not v or len(v) > 64 for v in racers.values()):
        raise ValueError("INVALID_HISTORIC_RACER_ID")
    if len(set(racers.values())) != 6:
        raise ValueError("REPEATED_RACER_ID")
    if any(v is not None and (not isinstance(v, str) or not v or len(v) > 64) for v in motors.values()):
        raise ValueError("INVALID_MOTOR_EPOCH")
    return second, third, racers[actual[1]], motors[actual[1]]


def build_historical_escape_counts(scope, target, events):
    """Return only selected counts; no outcome access or actual target result."""
    frozen, blocked = _target_context(scope, target)
    if not isinstance(events, list) or not events:
        raise ValueError("AUTHORIZED_HISTORICAL_COHORT_EMPTY")
    cutoff = date(int(scope["train_end"][:4]), int(scope["train_end"][4:6]), int(scope["train_end"][6:8]))
    layer_second, layer_third = {}, {}
    for layer in LAYERS:
        layer_second[layer], layer_third[layer] = _empty()
    seen = set()
    last_key = None
    for row in events:
        key = row.get("race_key") if isinstance(row, dict) else None
        if key in seen:
            raise ValueError("DUPLICATE_HISTORICAL_RACE")
        if last_key is not None and (not isinstance(key, str) or key <= last_key):
            raise ValueError("HISTORICAL_COHORT_NOT_CANONICALLY_ORDERED")
        seen.add(key)
        last_key = key
        s, t, racer, motor = _event(row, cutoff, frozen, blocked)
        layers = ["national"]
        if row["venue"] == target["target_venue"]:
            layers.append("venue")
            if target["target_c1_racer"] is not None and racer == target["target_c1_racer"]:
                layers.append("racer")
                if target["target_c1_motor_epoch"] is not None and motor == target["target_c1_motor_epoch"]:
                    layers.append("motor")
        for layer in layers:
            layer_second[layer][s] += 1
            layer_third[layer][s][t] += 1
    if not seen:
        raise ValueError("EMPTY_VERIFIED_COHORT")
    # A layer without a single observed event is missing, NOT a zero vector.
    second = {layer: (layer_second[layer] if sum(layer_second[layer].values()) else None)
              for layer in LAYERS}
    third = {
        s: {
            layer: (layer_third[layer][s] if second[layer] is not None else None)
            for layer in LAYERS
        } for s in sorted(TAIL)
    }
    grouped = {
        "second_by_actual_course": second,
        "third_by_actual_course_given_second": third,
    }
    counts_digest = hashlib.sha256((json.dumps({
        "historical_count_schema": MODEL,
        "target": target, "historical_race_ids": sorted(seen),
        "counts": grouped,
    }, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)+"\n").encode()).hexdigest()
    return {
        "schema": MODEL, "race_key": target["race_key"],
        "historical_events_verified_by_code": len(seen),
        "layer_event_n": {layer: sum(layer_second[layer].values()) for layer in LAYERS},
        "conditional_counts": grouped,
        "training_count_derivation_sha256": counts_digest,
        "source_manifest_sha256": target["historical_raw_manifest_sha256"],
        "event_rights_and_first_git_clock_independently_attested_by_code": False,
        "historical_data_loaded_or_fetched_by_function": False,
        "formal_results_touched": False, "site_promoted": False, "fresh_accuracy_proven": False,
    }
