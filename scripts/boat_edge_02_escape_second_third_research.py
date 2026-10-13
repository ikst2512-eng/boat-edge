"""Track 02: escape-by-ACTUAL-course-1 conditional second/third research kernel.

Reads no files, results, payouts, source sites or network. Count inputs MUST
come from separately licensed and authenticated, PRE-TARGET historical records
whose final actual course and winning kimarite were both confirmed. Pre-race
start-exhibition is a PROJECTION, never evidence of historical actual course.

This gives 20 course-conditioned relative masses summing to one, NOT a complete
120-way probability forecast. A separately calibrated P(escape world) and
other worlds are required before a full-race model can be considered.
"""
from __future__ import annotations

import hashlib
import json
import math
from datetime import date, datetime, timedelta, timezone

from boat_edge_02_hierarchical_conditional_research import _check_scope, _posterior

ID = "BOAT_EDGE_02_COURSE1_ESCAPE_2ND3RD_COND_RESEARCH_V1"
COURSES = frozenset(range(1, 7))
TAIL = frozenset(range(2, 7))
SHA_KEYS = ("source_snapshot_sha256", "historical_count_manifest_sha256")
STAGES = ("second_by_actual_course", "third_by_actual_course_given_second")


def _digest(payload):
    return hashlib.sha256((json.dumps(payload, sort_keys=True, ensure_ascii=False,
                                      separators=(",", ":"), allow_nan=False) + "\n").encode()).hexdigest()


def _proof(scope, race_key, evidence):
    _check_scope(scope, race_key)
    required = {
        "schema", "historical_population", "historical_finish_basis",
        "pre_result_entry_basis", "predicted_course_to_boat",
        "source_snapshot_sha256", "historical_count_manifest_sha256",
        "historical_count_rights_reviewed", "historical_cutoff",
        "no_target_day_history", "six_active_boats_no_scratch",
    }
    if not isinstance(evidence, dict) or set(evidence) != required:
        raise ValueError("EXPLICIT_ESCAPING_COURSE_PROOF_REQUIRED")
    if (evidence["schema"] != "BE02_ESCAPE_COURSE1_HISTORY_AND_ENTRY_SCOPE_V1" or
            evidence["historical_population"] != "RESULT_CONFIRMED_ACTUAL_COURSE1_ESCAPE_ONLY" or
            evidence["historical_finish_basis"] != "OFFICIAL_CONFIRMED_KIMARITE_NIGE_AND_ALL_THREE_FINISHERS" or
            evidence["pre_result_entry_basis"] != "OFFICIAL_START_EXHIBITION_PROJECTION_NOT_ACTUAL_ENTRY"):
        raise ValueError("ESCAPE_KIMARITE_OR_ENTRY_SEMANTICS_INVALID")
    if (evidence["historical_count_rights_reviewed"] is not True or
            evidence["no_target_day_history"] is not True or
            evidence["six_active_boats_no_scratch"] is not True):
        raise ValueError("RIGHTS_OR_PRE_RESULT_GUARD_MISSING")
    if evidence["historical_cutoff"] != scope["train_end"]:
        raise ValueError("HISTORICAL_CUTOFF_MISMATCH")
    if any(not isinstance(evidence[k], str) or len(evidence[k]) != 64 or
           any(c not in "0123456789abcdef" for c in evidence[k]) for k in SHA_KEYS):
        raise ValueError("HISTORY_AND_ENTRY_SHA_REQUIRED")
    mapping = evidence["predicted_course_to_boat"]
    if (not isinstance(mapping, dict) or set(mapping) != COURSES or
            any(type(v) is not int for v in mapping.values()) or
            set(mapping.values()) != COURSES):
        raise ValueError("PREDICTED_COURSE_TO_BOAT_NOT_SIX_PERMUTATION")
    return mapping


def _layer_count_consistency(groups):
    """Each historical cohort includes one second and one third per race.

    Reject inconsistent national / venue / racer / motor count denominators.
    A layer can be wholly missing (None), never silently zero-imputed.
    """
    if not isinstance(groups, dict) or set(groups) != set(STAGES):
        raise ValueError("SECOND_THIRD_COUNTS_REQUIRED")
    second, third = groups[STAGES[0]], groups[STAGES[1]]
    if not isinstance(second, dict) or set(second) != {"national", "venue", "racer", "motor"}:
        raise ValueError("SECOND_LAYERS_REQUIRED")
    if not isinstance(third, dict) or set(third) != TAIL:
        raise ValueError("THIRD_CONDITIONALS_REQUIRED")
    for s in sorted(TAIL):
        if not isinstance(third[s], dict) or set(third[s]) != set(second):
            raise ValueError("THIRD_LAYERS_REQUIRED")
    for layer in second:
        counts = second[layer]
        if counts is None:
            if any(third[s][layer] is not None for s in TAIL):
                raise ValueError("THIRD_COUNTS_WITHOUT_SECOND_COHORT")
            continue
        if not isinstance(counts, dict) or set(counts) != TAIL or any(
                type(n) is not int or n < 0 for n in counts.values()):
            raise ValueError("BAD_SECOND_COHORT_COUNTS")
        for s in TAIL:
            third_counts = third[s][layer]
            expected = TAIL - {s}
            if (not isinstance(third_counts, dict) or set(third_counts) != expected or
                    any(type(n) is not int or n < 0 for n in third_counts.values()) or
                    sum(third_counts.values()) != counts[s]):
                raise ValueError("SECOND_THIRD_COHORT_DENOMINATOR_MISMATCH")
    if second["national"] is None or sum(second["national"].values()) == 0:
        raise ValueError("NATIONAL_ESCAPE_COHORT_NOT_OBSERVED")


def estimate_escape_second_third(race_key, scope, evidence, historical_counts):
    """20 normalized outcomes conditional on COURSE 1 escaping.

    Records are keyed by HISTORICAL ACTUAL COURSE; converted to pre-race
    predicted BOAT number with an explicit official start-exhibition mapping.
    A pre-race prediction never claims this projected entry was the final one.
    """
    mapping = _proof(scope, race_key, evidence)
    _layer_count_consistency(historical_counts)
    second_p, second_used = _posterior(historical_counts[STAGES[0]], tuple(sorted(TAIL)))
    third_used, twenty = {}, []
    for second_course in sorted(TAIL):
        third_p, used = _posterior(
            historical_counts[STAGES[1]][second_course], tuple(sorted(TAIL - {second_course}))
        )
        third_used[str(second_course)] = used
        for third_course in sorted(TAIL - {second_course}):
            twenty.append({
                "boat_combo": f"{mapping[1]}-{mapping[second_course]}-{mapping[third_course]}",
                "conditional_relative_mass": second_p[second_course] * third_p[third_course],
                "second_actual_course_condition": second_course,
                "third_actual_course_condition": third_course,
            })
    twenty.sort(key=lambda row: (-row["conditional_relative_mass"], row["boat_combo"]))
    total = sum(row["conditional_relative_mass"] for row in twenty)
    if len(twenty) != 20 or len({row["boat_combo"] for row in twenty}) != 20 or not math.isclose(
            total, 1.0, abs_tol=1e-12):
        raise ValueError("INVALID_ESCAPE_20")
    return {
        "model_id": ID,
        "race_key": race_key,
        "conditional_event": "HISTORICALLY_VERIFIED_COURSE1_NIGE_WORLD",
        "conditional_head_boat_projection": mapping[1],
        "head_boat_not_assumed_boat1": True,
        "entry_is_provisional_not_verified_actual": True,
        "historical_license_and_sha_not_independently_authenticated": True,
        "historical_national_escape_event_n": sum(
            historical_counts[STAGES[0]]["national"].values()),
        "used_layers": {
            "second": second_used,
            "third_by_second_course": third_used,
        },
        "course_to_boat_mapping_sha256": _digest(mapping),
        "conditional_20": twenty,
        "conditional_top10": [r["boat_combo"] for r in twenty[:10]],
        "world_prior_probability": None,
        "full_120_ready": False,
        "calibrated": False,
        "fresh_accuracy_proven": False,
        "formal_fresh_result_read": False,
        "results_read": False,
        "promote_to_site": False,
        "real_wagers_authorized": False,
    }
