"""Track 02 conditional exhibition→final-entry research, never a result fetcher.

Operator supplies independently permission-approved historic *paired* records.
No filesystem, browser, network, protected outcome endpoint, site model update,
wager or current target result. Caller-provided rights/clock/SHA assertions are
not independently authenticated. All weights are relative, NOT calibrated
future actual-entry probabilities. This is different from the existing
frame→course marginal 720-way prior, and does not replicate V307/V317/V360.
"""
from __future__ import annotations

from datetime import datetime, timedelta
import itertools
import math
import re

from boat_edge_02_hierarchical_conditional_research import _check_scope, _date, RESEARCH_PROTECTED_DATES
from boat_edge_02_joint_entry_permutation_research import digest

ID = "BOAT_EDGE_02_PAIRED_EXHIBITION_TO_ACTUAL_ENTRY_RESEARCH_V1"
BOATS = frozenset(range(1, 7))
TRANSITIONS = tuple(itertools.permutations(range(1, 7)))
JST = timedelta(hours=9)
KEY = re.compile(r"20\d{6}-(?:0[1-9]|1\d|2[0-4])-(?:0[1-9]|1[0-2])\Z")
HEX = re.compile(r"[0-9a-f]{64}\Z")
EVIDENCE_KEYS = {
    "schema", "target_race_key", "target_venue", "target_exhibition_course_by_boat",
    "target_exhibition_mapping_sha256", "target_exhibition_first_seen_jst",
    "training_source_manifest_sha256", "permission_evidence_sha256",
    "rights_reviewed_for_historic_pairs", "history_cutoff",
    "current_locked_formal_dates", "historic_course_final_is_official",
    "historic_exhibition_is_pre_result", "no_target_actual_course_or_outcome",
}
ROW_KEYS = {
    "race_key", "venue", "exhibition_course_by_boat", "actual_course_by_boat",
    "exhibition_first_seen_jst", "final_actual_course_first_seen_jst",
    "exhibition_source_sha256", "final_course_source_sha256",
    "has_six_active_boats_no_scratch", "source_licensed_for_research",
}
SHRINKAGE_N = 30.0   # fixed prior count: must be retuned only on future train folds
MIN_NATIONAL = 30
MIN_VENUE = 8


def _seen(value):
    if not isinstance(value, str):
        raise ValueError("PAIRED_ENTRY_TIMESTAMP_REQUIRED")
    try:
        t = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError("PAIRED_ENTRY_TIMESTAMP_INVALID") from exc
    if t.tzinfo is None or t.utcoffset() != JST:
        raise ValueError("PAIRED_ENTRY_JST_OFFSET_REQUIRED")
    return t


def _six(mapping, what):
    if (not isinstance(mapping, dict) or set(mapping) != BOATS
            or any(type(v) is not int for v in mapping.values())
            or set(mapping.values()) != BOATS):
        raise ValueError("SIX_ACTUAL_VS_EXHIBITION_PERMUTATION_REQUIRED:" + what)
    return mapping


def _sha(value):
    if not isinstance(value, str) or HEX.fullmatch(value) is None:
        raise ValueError("PAIRED_ENTRY_SHA256_REQUIRED")


def _event_key(key):
    if not isinstance(key, str) or KEY.fullmatch(key) is None:
        raise ValueError("BAD_HISTORIC_PAIRED_RACE_KEY")
    _date(key[:8])
    return key


def _validate(race_key, scope, evidence):
    _check_scope(scope, race_key)
    if not isinstance(evidence, dict) or set(evidence) != EVIDENCE_KEYS:
        raise ValueError("PAIRED_ENTRY_EXACT_EVIDENCE_REQUIRED")
    if evidence["schema"] != "BE02_PAIRED_EXHIBITION_ACTUAL_TRAIN_V1" or evidence["target_race_key"] != race_key:
        raise ValueError("PAIRED_ENTRY_RACE_ID_MISMATCH")
    venue = int(race_key.split("-")[1])
    if type(evidence["target_venue"]) is not int or evidence["target_venue"] != venue:
        raise ValueError("PAIRED_ENTRY_TARGET_VENUE_MISMATCH")
    if (evidence["rights_reviewed_for_historic_pairs"] is not True
            or evidence["historic_course_final_is_official"] is not True
            or evidence["historic_exhibition_is_pre_result"] is not True
            or evidence["no_target_actual_course_or_outcome"] is not True):
        raise ValueError("PAIRED_ENTRY_RIGHTS_AND_TEMPORAL_GUARD")
    _six(evidence["target_exhibition_course_by_boat"], "TARGET")
    _sha(evidence["target_exhibition_mapping_sha256"])
    _sha(evidence["training_source_manifest_sha256"])
    _sha(evidence["permission_evidence_sha256"])
    if (digest(evidence["target_exhibition_course_by_boat"]) != evidence["target_exhibition_mapping_sha256"]
            or evidence["training_source_manifest_sha256"] != scope["source_manifest_sha256"]
            or evidence["permission_evidence_sha256"] != scope["reviewed_permission_evidence_sha256"]):
        raise ValueError("PAIRED_ENTRY_SOURCE_SHA_MISMATCH")
    if evidence["history_cutoff"] != scope["train_end"]:
        raise ValueError("PAIRED_ENTRY_HISTORY_CUTOFF_MISMATCH")
    freeze = _seen(scope["first_frozen_at"])
    exhib_seen = _seen(evidence["target_exhibition_first_seen_jst"])
    if exhib_seen.date() != _date(race_key[:8]) or exhib_seen > freeze:
        raise ValueError("TARGET_EXHIBITION_NOT_AVAILABLE_AT_FREEZE")
    blocked = evidence["current_locked_formal_dates"]
    if (not isinstance(blocked, list) or not blocked
            or any(not isinstance(x, str) or not re.fullmatch(r"20\d{6}", x) for x in blocked)
            or len(set(blocked)) != len(blocked)):
        raise ValueError("DYNAMIC_FORMAL_PROTECTED_DATE_AUDIT_REQUIRED")
    if race_key[:8] in blocked:
        raise ValueError("FORMAL_PROTECTED_TARGET_DATE")
    return venue, freeze, set(blocked) | RESEARCH_PROTECTED_DATES


def estimate_exhibition_conditioned_entry(race_key, scope, evidence, historic_rows):
    """720 hypothetical BOAT->final COURSE assignments conditioned on exhibition.

    Venue transition counts are shrunk toward directly *observed* national
    paired transition frequencies. Unobserved exact transitions remain zero,
    not synthetic pseudoevents. Training pairs must cover same-event full-six
    exhibition AND actual official courses before cutoff and freeze.
    """
    venue, freeze, blocked = _validate(race_key, scope, evidence)
    if not isinstance(historic_rows, list) or not historic_rows:
        raise ValueError("PAIRED_ENTRY_HISTORY_NOT_SUPPLIED")
    national = {t: 0 for t in TRANSITIONS}
    local = {t: 0 for t in TRANSITIONS}
    previous = None
    for row in historic_rows:
        if not isinstance(row, dict) or set(row) != ROW_KEYS:
            raise ValueError("PAIRED_ENTRY_HISTORIC_ROW_SCHEMA_INVALID")
        k = _event_key(row["race_key"])
        if previous is not None and k <= previous:
            raise ValueError("PAIRED_ENTRY_DUPLICATE_OR_UNSORTED_RACES")
        previous = k
        if k[:8] in blocked:
            raise ValueError("PAIRED_ENTRY_PROTECTED_FORMAL_HISTORIC_RACE")
        if _date(k[:8]) > _date(scope["train_end"]):
            raise ValueError("PAIRED_ENTRY_HISTORY_TARGET_DAY_LEAK")
        race_venue = int(k.split("-")[1])
        if type(row["venue"]) is not int or not 1 <= race_venue <= 24 or row["venue"] != race_venue:
            raise ValueError("PAIRED_ENTRY_HISTORIC_VENUE_MISMATCH")
        if (row["has_six_active_boats_no_scratch"] is not True
                or row["source_licensed_for_research"] is not True):
            raise ValueError("PAIRED_ENTRY_HISTORIC_RIGHTS_OR_SCRATCH")
        a = _six(row["exhibition_course_by_boat"], "HIST_EXHIBITION")
        b = _six(row["actual_course_by_boat"], "HIST_ACTUAL")
        for name in ("exhibition_source_sha256", "final_course_source_sha256"):
            _sha(row[name])
        exhib_t = _seen(row["exhibition_first_seen_jst"])
        actual_t = _seen(row["final_actual_course_first_seen_jst"])
        if (exhib_t.date() != _date(k[:8]) or not exhib_t < actual_t
                or not actual_t < freeze):
            raise ValueError("PAIRED_ENTRY_HISTORIC_ASOF_NOT_PROVED")
        # The boat occupying historical exhibition course e subsequently
        # occupies final actual course transition[e]. This is independent of
        # named boat # and always forms a single bijection over six courses.
        boat_from_exhib = {course: boat for boat, course in a.items()}
        transition = tuple(b[boat_from_exhib[e]] for e in range(1, 7))
        national[transition] += 1
        if race_venue == venue:
            local[transition] += 1
    n_nat, n_loc = sum(national.values()), sum(local.values())
    if n_nat < MIN_NATIONAL or n_loc < MIN_VENUE:
        raise ValueError("PAIRED_ENTRY_COHORT_TOO_SPARSE")
    exhib = evidence["target_exhibition_course_by_boat"]
    ranked = []
    for t in TRANSITIONS:
        # No fabricated "identity prior": shrink ONLY toward observed national
        # joint exhibition→actual transitions, not uniform 1/720.
        prob = (local[t] + SHRINKAGE_N * national[t] / n_nat) / (n_loc + SHRINKAGE_N)
        final_by_boat = tuple(t[exhib[boat]-1] for boat in range(1, 7))
        ranked.append((final_by_boat, prob))
    ranked.sort(key=lambda x: (-x[1], x[0]))
    total = sum(prob for _, prob in ranked)
    if (len(ranked) != 720 or
            len({perm for perm,_ in ranked}) != 720 or
            not math.isclose(total,1.0,rel_tol=0,abs_tol=1e-11)):
        raise ValueError("PAIRED_ENTRY_720_NORMALIZATION_FAILED")
    marginal = {str(b): {str(c):0.0 for c in range(1,7)} for b in range(1,7)}
    for perm,prob in ranked:
        for boat,course in enumerate(perm,1):
            marginal[str(boat)][str(course)] += prob
    if (any(not math.isclose(sum(marginal[str(b)].values()),1.0,abs_tol=1e-11)
            for b in range(1,7))
        or any(not math.isclose(
                sum(marginal[str(b)][str(c)] for b in range(1,7)),
                1.0,abs_tol=1e-11) for c in range(1,7))):
        raise ValueError("PAIRED_ENTRY_720_MARGINAL_INVARIANT_FAILED")
    histogram = {
        "national": {"-".join(map(str,k)): v for k,v in national.items() if v},
        "venue": {"-".join(map(str,k)): v for k,v in local.items() if v},
        "national_n": n_nat, "venue_n": n_loc,
        "target_exhibition_sha256": evidence["target_exhibition_mapping_sha256"],
        "history_cutoff": scope["train_end"],
    }
    return {
        "model_id": ID, "race_key": race_key,
        "scope": "RESEARCH_ONLY_CONDITIONAL_EXHIBITION_TO_ACTUAL_NOT_CALIBRATED",
        "training_end": scope["train_end"],
        "historical_national_paired_events_n": n_nat,
        "historical_same_venue_paired_events_n": n_loc,
        "distinct_national_observed_transition_patterns": sum(bool(v) for v in national.values()),
        "distinct_venue_observed_transition_patterns": sum(bool(v) for v in local.values()),
        "observed_paired_counts_sha256": digest(histogram),
        "target_exhibition_mapping_sha256": evidence["target_exhibition_mapping_sha256"],
        "training_source_manifest_sha256": evidence["training_source_manifest_sha256"],
        "permission_evidence_sha256": evidence["permission_evidence_sha256"],
        "target_exhibition_permutation_used_in_mapping": True,
        "historic_transition_counts_conditioned_on_exact_exhibition_pattern": False,
        "full_conditional_entry_posterior_calibrated": False,
        "same_race_actual_entry_known": False,
        "entry_distribution_prospectively_calibrated": False,
        "rights_sha_and_first_seen_independently_authenticated": False,
        "missing_history_or_actual_entry_imputed": False,
        "ranked_720": [
            {"course_by_boat": list(perm), "relative_model_mass": prob}
            for perm,prob in ranked
        ],
        "course_marginal_by_boat": marginal,
        "formal_results_read": False, "target_outcome_read": False,
        "production_eligible": False, "wagers_authorized": False,
        "top3_top5_top10_improvement_proven": False,
    }
