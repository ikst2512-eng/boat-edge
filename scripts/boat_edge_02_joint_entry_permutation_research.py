"""Track 02 — synthetic/permission-reviewed six-boat joint entry research.

Unlike V360's *known provisional exhibition permutation*, this estimates a
research-only distribution over all 6! = 720 possible entry permutations from
complete, historical, same-cohort boat(frame)→actual-course observation counts.

No network/files/official result access, no target race result, no odds, no
production model changes, no Formal Fresh. Source permission and first-seen
metadata remain *self-reported*, not independently authenticated here.
"""
from __future__ import annotations

from datetime import datetime, timedelta
import hashlib
import itertools
import json
import math
from urllib.parse import urlparse

from boat_edge_02_hierarchical_conditional_research import _check_scope, _date

ID = "BOAT_EDGE_02_JOINT_SIX_ENTRY_PERMUTATIONS_RESEARCH_V1"
BOATS = tuple(range(1, 7))
PERMS = tuple(itertools.permutations(BOATS))
REQUIRED = {
    "schema", "source_class", "source_url", "venue", "historical_period_start",
    "historical_period_end", "same_cohort_six_boat_races_n",
    "boat_frame_course_observed_counts", "counts_sha256",
    "source_manifest_sha256", "permission_evidence_sha256",
    "rights_reviewed_for_training", "first_source_seen_at_jst",
    "source_event_times_before_target", "six_boats_and_no_scratch_verified",
    "actual_target_course_not_used", "target_result_not_used",
}


def canonical(obj):
    return (json.dumps(obj, ensure_ascii=False, sort_keys=True,
                       separators=(",", ":"), allow_nan=False) + "\n").encode("utf-8")


def digest(obj):
    return hashlib.sha256(canonical(obj)).hexdigest()


def joint_entry_distribution(race_key, scope, evidence):
    """Return 720 empirical relative masses, never calibrated probabilities."""
    _check_scope(scope, race_key)
    if not isinstance(evidence, dict) or set(evidence) != REQUIRED:
        raise ValueError("JOINT_ENTRY_EXACT_EVIDENCE_SCHEMA_REQUIRED")
    if (evidence["schema"] != "BE02_JOINT_ENTRY_OBSERVED_COUNTS_V1"
            or evidence["source_class"] != "REVIEWED_AUTHORIZED_OFFICIAL_HISTORICAL_ACTUAL_ENTRY"
            or evidence["rights_reviewed_for_training"] is not True
            or evidence["source_event_times_before_target"] is not True
            or evidence["six_boats_and_no_scratch_verified"] is not True
            or evidence["actual_target_course_not_used"] is not True
            or evidence["target_result_not_used"] is not True):
        raise ValueError("ENTRY_RIGHTS_OR_PRE_RESULT_SEMANTICS_INVALID")
    uri = evidence["source_url"]
    if (not isinstance(uri, str) or (p := urlparse(uri)).scheme != "https" or
            not p.hostname or p.username or p.password or p.fragment or
            p.hostname.lower() not in {
                "www.boatrace.jp", "boatrace.jp",
                "www.boatrace-biwako.jp", "boatrace-biwako.jp",
            }):
        # Strict allowlist for this research hypothesis, NOT permission to fetch
        # those hosts. Other venue domains require a reviewed new contract.
        raise ValueError("OFFICIAL_SOURCE_URL_REQUIRED")
    if (evidence["source_manifest_sha256"] != scope["source_manifest_sha256"]
            or evidence["permission_evidence_sha256"] != scope["reviewed_permission_evidence_sha256"]):
        raise ValueError("ENTRY_SOURCE_OR_PERMISSION_SHA_MISMATCH")
    venue = int(race_key.split("-")[1])
    if type(evidence["venue"]) is not int or evidence["venue"] != venue:
        raise ValueError("ENTRY_VENUE_MISMATCH")
    first = _date(evidence["historical_period_start"])
    last = _date(evidence["historical_period_end"])
    cutoff = _date(scope["train_end"])
    if first > last or last > cutoff:
        raise ValueError("ENTRY_HISTORICAL_PERIOD_FUTURE_LEAK")
    try:
        seen = datetime.fromisoformat(evidence["first_source_seen_at_jst"])
        frozen = datetime.fromisoformat(scope["first_frozen_at"])
    except (TypeError, ValueError) as exc:
        raise ValueError("ENTRY_SOURCE_CLOCK_INVALID") from exc
    if (seen.tzinfo is None or seen.utcoffset() != timedelta(hours=9)
            or seen >= frozen):
        raise ValueError("ENTRY_SOURCE_NOT_PROVEN_PRE_FREEZE")
    n = evidence["same_cohort_six_boat_races_n"]
    if type(n) is not int or n < 30:
        raise ValueError("ENTRY_SAME_COHORT_MINIMUM_N_NOT_MET")
    counts = evidence["boat_frame_course_observed_counts"]
    if not isinstance(counts, dict) or set(counts) != set(BOATS):
        raise ValueError("ENTRY_SIX_BOAT_ROWS_REQUIRED")
    if any(not isinstance(row, dict) or set(row) != set(BOATS)
           for row in counts.values()):
        raise ValueError("ENTRY_SIX_COURSE_COLUMNS_REQUIRED")
    if any(type(x) is not int or x < 0 for row in counts.values() for x in row.values()):
        raise ValueError("ENTRY_NONNEGATIVE_INTEGER_COUNTS_REQUIRED")
    if any(sum(counts[b].values()) != n for b in BOATS):
        raise ValueError("ENTRY_ROWS_NOT_SAME_OBSERVED_POPULATION")
    if any(sum(counts[b][c] for b in BOATS) != n for c in BOATS):
        raise ValueError("ENTRY_COLUMNS_NOT_SAME_OBSERVED_POPULATION")
    if evidence["counts_sha256"] != digest(counts):
        raise ValueError("ENTRY_COUNT_CONTENT_HASH_MISMATCH")
    # Marginal frequency conditioning on the global permutation constraint.
    # This does NOT assert the six boat choices are truly independent.
    props = {b: {c: counts[b][c] / n for c in BOATS} for b in BOATS}
    likelihoods = [(p, math.prod(props[boat][course] for boat, course in enumerate(p, 1)))
                   for p in PERMS]
    z = sum(weight for _, weight in likelihoods)
    if z <= 0 or not math.isfinite(z):
        raise ValueError("NO_JOINT_ENTRY_PERMUTATION_SUPPORT")
    ranked = sorted(((p, w/z) for p, w in likelihoods), key=lambda x: (-x[1], x[0]))
    marginals = {str(b): {str(c): 0.0 for c in BOATS} for b in BOATS}
    for p, weight in ranked:
        for b, c in enumerate(p, 1):
            marginals[str(b)][str(c)] += weight
    if len(ranked) != 720 or abs(sum(w for _, w in ranked)-1) > 1e-12:
        raise ValueError("ENTRY_720_INVARIANT_FAIL")
    if any(abs(sum(marginals[str(b)].values())-1) > 1e-12 for b in BOATS):
        raise ValueError("ENTRY_BOAT_MARGINAL_INVARIANT_FAIL")
    if any(abs(sum(marginals[str(b)][str(c)] for b in BOATS)-1) > 1e-12 for c in BOATS):
        raise ValueError("ENTRY_COURSE_OCCUPANCY_INVARIANT_FAIL")
    return {
        "model_id": ID,
        "race_key": race_key,
        "scope": "RESEARCH_ONLY_UNCALIBRATED_PROVISIONAL_ENTRY_NOT_ACTUAL",
        "source_count_sha256": digest(counts),
        "source_permission_and_first_seen_authenticated_by_function": False,
        "training_end": scope["train_end"],
        "historical_races_n": n,
        "distinct_full_entry_permutations": 720,
        "ranked_720": [{"course_by_boat": list(p), "relative_model_mass": w}
                        for p, w in ranked],
        "top10_provisional_course_assignments": [list(p) for p, _ in ranked[:10]],
        "course_marginal_by_boat": marginals,
        "same_race_actual_entry_known": False,
        "missing_values_imputed": False,
        "full_120_trifecta_ready": False,
        "top3_top5_top10_hit_rate_improvement_proven": False,
        "formal_results_seen": False,
        "production_eligible": False,
        "wagers_authorized": False,
    }
