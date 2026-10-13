"""Track 02: isolate entry uncertainty from venue-course effects, TopK hypothesis.

Use existing V307's COURSE 120-ranker and V317's mapper for the fixed,
known exhibition parent. Hypothetical alternative entry permutations cannot
be labelled an observed start exhibition (V317 only supports actual asserted
or observed exhibition labels), so the counterfactual branch explicitly
translates hypothetical course combos to BOAT tickets without a false source
claim. No production code, I/O, target outcomes, score, wager or Formal Fresh.

Entry weights are relative, NOT calibrated actual-entry probabilities.
120-ticket masses are research-only relative masses, NOT race win probabilities.
Any reported source hashes / permission / first-seen are caller assertions.
"""
from __future__ import annotations

from datetime import date
import itertools
import math
import re

from boat_edge_02_hierarchical_conditional_research import _check_scope, _date
from boat_edge_02_joint_entry_permutation_research import (
    joint_entry_distribution, digest, ID as ENTRY_ID,
)
from boat_edge_v307_pl120_research import rank_120
from boat_edge_v317_ticket_mapper import map_course_mass_to_boat_tickets

MODEL = "BOAT_EDGE_02_ENTRY_MARGINALIZED_TOPK_ABLATION_V1"
NO_FACTOR = "BOAT_EDGE_02_V307_EXHIBITION_NO_COURSE_FACTOR_CONTROL_V1"
BASELINE = "BOAT_EDGE_02_V307_EXHIBITION_SINGLE_ENTRY_BASELINE_V1"
CANDIDATE = "BOAT_EDGE_02_V307_JOINT_ENTRY_MARGINAL_RESEARCH_V1"
BOATS = frozenset(range(1, 7))
COMBOS = frozenset("-".join(map(str, k)) for k in itertools.permutations(range(1, 7), 3))
REQUIRED = {
    "schema", "race_key", "target_source_sha256", "entry_mapping_sha256",
    "source_permission_evidence_sha256", "reference_exhibition_course_by_boat",
    "boat_strength_by_boat", "course_factor_by_course", "course_factor_training_end",
    "course_factor_manifest_sha256", "course_factor_permission_reviewed",
    "frozen_pre_result_evidence_only", "six_active_boats_no_scratch",
    "not_using_target_actual_entry", "not_using_target_outcome",
}
HEX = re.compile(r"[0-9a-f]{64}\Z")


def _validate_values(a, expected, name, lo=0):
    if not isinstance(a, dict) or set(a) != expected:
        raise ValueError("SIX_LABELLED_" + name + "_REQUIRED")
    if any(type(v) not in (int, float) or not math.isfinite(v) or v <= lo for v in a.values()):
        raise ValueError("POSITIVE_FINITE_" + name + "_REQUIRED")
    return {k: float(a[k]) for k in sorted(expected)}


def _doc(model, key, cfg, rows):
    return {
        "model_id": model,
        "race_key": key,
        "target_source_sha256": cfg["target_source_sha256"],
        "entry_mapping_sha256": cfg["entry_mapping_sha256"],
        "ranked_120": rows,
    }


def _ranked(masses):
    if set(masses) != COMBOS:
        raise ValueError("MARGINAL_TRIFECTAS_NOT_EXACT_120")
    if any(type(v) not in (float, int) or not math.isfinite(v) or v <= 0 for v in masses.values()):
        raise ValueError("MARGINAL_120_MASS_INVALID")
    z = sum(masses.values())
    if not math.isclose(z, 1, rel_tol=0, abs_tol=2e-9):
        raise ValueError("MARGINAL_120_NOT_NORMALIZED")
    rows = sorted(masses.items(), key=lambda x: (-x[1], x[0]))
    return [{"boat_combo": k, "relative_model_mass": p/z} for k, p in rows]


def prepare_entry_topk_ablation(race_key, scope, cfg, entry_evidence):
    """Deterministic pure A/B candidate generation, NEVER live model promotion."""
    _check_scope(scope, race_key)
    if not isinstance(cfg, dict) or set(cfg) != REQUIRED:
        raise ValueError("ENTRY_ABLATION_EXACT_CONTEXT_REQUIRED")
    if cfg["schema"] != "BE02_ENTRY_TOPK_PRE_RESULT_CONTEXT_V1" or cfg["race_key"] != race_key:
        raise ValueError("ENTRY_ABLATION_RACE_SCOPE_MISMATCH")
    if (cfg["frozen_pre_result_evidence_only"] is not True or
            cfg["six_active_boats_no_scratch"] is not True or
            cfg["not_using_target_actual_entry"] is not True or
            cfg["not_using_target_outcome"] is not True or
            cfg["course_factor_permission_reviewed"] is not True):
        raise ValueError("ENTRY_ABLATION_RIGHTS_PRE_RESULT_GUARD")
    for field in ("target_source_sha256", "entry_mapping_sha256",
                  "source_permission_evidence_sha256", "course_factor_manifest_sha256"):
        if not isinstance(cfg[field], str) or not HEX.fullmatch(cfg[field]):
            raise ValueError("ENTRY_ABLATION_PROVENANCE_REQUIRED")
    if cfg["source_permission_evidence_sha256"] != scope["reviewed_permission_evidence_sha256"]:
        raise ValueError("ENTRY_ABLATION_PERMISSION_SHA_MISMATCH")
    if _date(cfg["course_factor_training_end"]) > _date(scope["train_end"]):
        raise ValueError("COURSE_FACTOR_TRAINING_AFTER_HISTORICAL_CUTOFF")
    observed = cfg["reference_exhibition_course_by_boat"]
    if (not isinstance(observed, dict) or set(observed) != BOATS or
            any(type(v) is not int for v in observed.values()) or
            set(observed.values()) != BOATS):
        raise ValueError("EXHIBITION_PERMUTATION_NOT_SIX")
    if cfg["entry_mapping_sha256"] != digest(observed):
        raise ValueError("EXHIBITION_MAPPING_SHA_MISMATCH")
    strengths = _validate_values(cfg["boat_strength_by_boat"], BOATS, "BOAT_STRENGTH")
    factors = _validate_values(cfg["course_factor_by_course"], BOATS, "COURSE_FACTOR")
    if cfg["course_factor_manifest_sha256"] != digest(factors):
        raise ValueError("COURSE_FACTOR_CONTENT_SHA_MISMATCH")
    entry = joint_entry_distribution(race_key, scope, entry_evidence)
    if (entry["model_id"] != ENTRY_ID or entry["race_key"] != race_key or
            entry["source_permission_and_first_seen_authenticated_by_function"] is not False or
            entry["full_120_trifecta_ready"] is not False or
            entry["formal_results_seen"] is not False):
        raise ValueError("JOINT_ENTRY_RESEARCH_ONLY_INVARIANTS")
    # Control A: original V307 research strengths with no new venue factor.
    # Control B: exactly the same exhibition mapping with a frozen course factor.
    # Candidate C: same factor and strengths as B, but uncertain joint entry.
    # Hence A→B isolates the new factor, while B→C isolates entry uncertainty.
    unadjusted = rank_120({course: strengths[boat] for boat, course in observed.items()})
    unadjusted_mapped = map_course_mass_to_boat_tickets(
        unadjusted, observed, "START_EXHIBITION_PROVISIONAL")
    no_factor = _ranked({row["boat_combo"]: row["relative_model_mass"]
                         for row in unadjusted_mapped["ranked_120_boat"]})
    prior_weights = {course: strengths[boat] * factors[course]
                     for boat, course in observed.items()}
    base_ranked = rank_120(prior_weights)
    base_mapped = map_course_mass_to_boat_tickets(
        base_ranked, observed, "START_EXHIBITION_PROVISIONAL")
    baseline = _ranked({
        row["boat_combo"]: row["relative_model_mass"]
        for row in base_mapped["ranked_120_boat"]
    })
    result_mass = {key: 0.0 for key in COMBOS}
    present = 0
    # The counterfactual entry permutation is NOT actual course and is NOT
    # another measured start exhibition. Only hypothetical lane assignment.
    for row in entry["ranked_720"]:
        mass = row["relative_model_mass"]
        if mass == 0:
            continue
        present += 1
        course_by_boat = {boat: row["course_by_boat"][boat-1] for boat in BOATS}
        boat_by_course = {course: boat for boat, course in course_by_boat.items()}
        weights = {course: strengths[boat] * factors[course]
                   for boat, course in course_by_boat.items()}
        for ccombo, prob in rank_120(weights):
            bcombo = "-".join(str(boat_by_course[int(c)]) for c in ccombo.split("-"))
            result_mass[bcombo] += mass * prob
    candidate = _ranked(result_mass)
    no_factor_top = [r["boat_combo"] for r in no_factor[:10]]
    base_top = [r["boat_combo"] for r in baseline[:10]]
    candidate_top = [r["boat_combo"] for r in candidate[:10]]
    def l1(left, right):
        lookup = {r["boat_combo"]: r["relative_model_mass"] for r in right}
        return sum(abs(row["relative_model_mass"] - lookup[row["boat_combo"]])
                   for row in left)
    factor_only_distance = l1(no_factor, baseline)
    distance = l1(baseline, candidate)

    def topk_delta(left, right):
        # This only measures how many boat tickets change, NOT accuracy.
        return {str(k): {
            "removed_boat_tickets": sorted(set(left[:k]) - set(right[:k])),
            "added_boat_tickets": sorted(set(right[:k]) - set(left[:k])),
            "changed_ticket_count_per_side": len(set(left[:k]) - set(right[:k])),
            "ordered_topk_identical": left[:k] == right[:k],
        } for k in (3, 5, 10)}

    def head_marginal(rows):
        out = {str(b): 0.0 for b in range(1, 7)}
        for row in rows:
            out[row["boat_combo"].split("-")[0]] += row["relative_model_mass"]
        if not math.isclose(sum(out.values()), 1.0, rel_tol=0, abs_tol=2e-10):
            raise ValueError("HEAD_MASS_NOT_NORMALIZED")
        return out

    a_head, b_head, c_head = (head_marginal(rows) for rows in
                              (no_factor, baseline, candidate))
    a_first_head = max(a_head, key=lambda k: (a_head[k], -int(k)))
    b_first_head = max(b_head, key=lambda k: (b_head[k], -int(k)))
    c_first_head = max(c_head, key=lambda k: (c_head[k], -int(k)))
    return {
        "schema": MODEL,
        "race_key": race_key,
        "no_factor_control_ranking_document": _doc(NO_FACTOR, race_key, cfg, no_factor),
        "baseline_ranking_document": _doc(BASELINE, race_key, cfg, baseline),
        "candidate_ranking_document": _doc(CANDIDATE, race_key, cfg, candidate),
        "no_factor_control_top3": no_factor_top[:3],
        "no_factor_control_top5": no_factor_top[:5],
        "no_factor_control_top10": no_factor_top,
        "baseline_top3": base_top[:3],
        "candidate_top3": candidate_top[:3],
        "baseline_top5": base_top[:5],
        "candidate_top5": candidate_top[:5],
        "baseline_top10": base_top,
        "candidate_top10": candidate_top,
        "entry_permutations_considered": 720,
        "entry_permutations_nonzero_weight": present,
        "entry_count_sha256": entry["source_count_sha256"],
        "factor_manifest_sha256": cfg["course_factor_manifest_sha256"],
        "entry_weight_semantics": "VENUE_FRAME_ACTUAL_COURSE_MARGINAL_PRIOR_NOT_P_OF_FINAL_ENTRY_GIVEN_TODAY_EXHIBITION",
        "live_exhibition_conditioned_entry_transition_learned": False,
        "entry_720_relative_weights_are_not_calibrated_posterior": True,
        "factor_only_mass_l1_not_hit_improvement": factor_only_distance,
        "topk_membership_a_to_b_not_hit_rates": topk_delta(no_factor_top, base_top),
        "topk_membership_b_to_c_not_hit_rates": topk_delta(base_top, candidate_top),
        "head_relative_mass_a": a_head,
        "head_relative_mass_b": b_head,
        "head_relative_mass_c": c_head,
        "top_head_boat_a": int(a_first_head),
        "top_head_boat_b": int(b_first_head),
        "top_head_boat_c": int(c_first_head),
        "head_top1_change_a_to_b": a_first_head != b_first_head,
        "head_top1_change_b_to_c": b_first_head != c_first_head,
        "model_ranking_change_is_not_real_accuracy_gain": True,
        "mass_l1_research_distance_not_hit_improvement": distance,
        "three_arm_predeclared_ablation": "A_no_factor__B_fixed_exhibition_with_course_factor__C_joint_entry_with_same_factor",
        "change_is_entry_uncertainty_only_at_fixed_strengths_and_factors": True,
        "baseline_entry_is_observed_exhibition_not_actual": True,
        "candidate_entry_is_hypothetical_permutation_not_actual": True,
        "actual_target_course_known": False,
        "calibration_validated": False,
        "head_top3_top5_top10_improvement_proven": False,
        "source_rights_and_first_git_time_independently_verified": False,
        "actual_results_or_formal_read": False,
        "production_eligible": False,
        "wagers_authorized": False,
    }
