"""R08/R09 isolated as-of ST-distribution and exhibition-to-final research.

Inputs: operator supplied, historically authorized *sufficient statistics*
and the optional contemporary OFFICIAL exhibition reading. No network/files/
result pages/odds/current actual ST; nothing here changes CURRENT weights.
Never copy externally claimed BOATRACEDATA correlation into this calculation.
"""
from __future__ import annotations

from datetime import datetime, timezone, timedelta
import math

from boat_edge_02_hierarchical_conditional_research import _check_scope

ID = "BOAT_EDGE_02_ST_DISTRIBUTION_AND_PAIRED_RESIDUAL_RESEARCH_V1"
ST_FIELDS = {
    "training_n", "top_start_count", "final_st_sum", "final_st_square_sum",
    "paired_n", "paired_ex_sum", "paired_final_sum",
    "paired_ex_square_sum", "paired_final_square_sum", "paired_ex_final_product_sum",
}
BOATS = set(range(1, 7))
SHRINK_PAIRS = 50.0
TOP_RATE_PRIOR_N = 12.0
TOP_RATE_PRIOR = 1 / 6


def _moment_variance(sum_x, sq_x, n):
    if n == 0:
        return None
    var = sq_x / n - (sum_x / n)**2
    if var < -1e-8:
        raise ValueError("INCONSISTENT_ST_MOMENTS")
    return max(0., var)


def derive_st_signals(race_key, scope, evidence, history):
    """Research features only, historical paired moments strictly pre-target."""
    _check_scope(scope, race_key)
    if not isinstance(evidence, dict) or set(evidence) != {
        "schema", "provenance", "six_boats_verified_no_scratch",
        "historical_finish_st_is_earlier_than_target",
        "source_rights_reviewed", "official_exhibition_only",
        "race_exhibition_observed_at_jst", "race_exhibition_by_boat",
    }:
        raise ValueError("ST_EVIDENCE_SCHEMA_REQUIRED")
    if (evidence["schema"] != "BE02_ST_PRE_RESULT_PROOF_V1" or
            evidence["provenance"] != scope["source_manifest_sha256"] or
            evidence["six_boats_verified_no_scratch"] is not True or
            evidence["historical_finish_st_is_earlier_than_target"] is not True or
            evidence["source_rights_reviewed"] is not True or
            evidence["official_exhibition_only"] is not True):
        raise ValueError("ST_SOURCE_OR_RIGHTS_OR_TEMPORAL_PROOF_REQUIRED")
    if not isinstance(history, dict) or set(history) != BOATS:
        raise ValueError("SIX_BOAT_HISTORY_REQUIRED")
    exhibition = evidence["race_exhibition_by_boat"]
    if not isinstance(exhibition, dict) or set(exhibition) != BOATS:
        raise ValueError("SIX_BOAT_EXHIBITION_FIELDS_REQUIRED")
    try:
        seen = datetime.fromisoformat(evidence["race_exhibition_observed_at_jst"])
        frozen = datetime.fromisoformat(scope["first_frozen_at"])
    except (TypeError, ValueError) as exc:
        raise ValueError("INVALID_EXHIBITION_TIMESTAMP") from exc
    if (seen.tzinfo is None or seen.utcoffset() != timedelta(hours=9)
            or seen > frozen or seen.date() != frozen.date()):
        raise ValueError("EXHIBITION_NOT_PROVEN_BEFORE_FREEZE")
    rows = []
    for boat in sorted(BOATS):
        row = history[boat]
        if not isinstance(row, dict) or set(row) != ST_FIELDS:
            raise ValueError("TRAINING_ST_MOMENTS_SCHEMA_INVALID")
        n, m, top = row["training_n"], row["paired_n"], row["top_start_count"]
        if (type(n) is not int or n < 0 or type(m) is not int or
                m < 0 or m > n or type(top) is not int or top < 0 or top > n):
            raise ValueError("TRAINING_OR_PAIRED_COUNTS_INVALID")
        sums = [row[k] for k in ST_FIELDS if k not in (
            "training_n", "paired_n", "top_start_count")]
        if any(type(x) not in (int,float) or not math.isfinite(x) or x < 0 for x in sums):
            raise ValueError("TRAINING_ST_MOMENTS_INVALID")
        if (n == 0 and (top != 0 or row["final_st_sum"] != 0 or row["final_st_square_sum"] != 0)
                or m == 0 and any(row[k] != 0 for k in ST_FIELDS if k.startswith("paired_") and k != "paired_n")):
            raise ValueError("EMPTY_HISTORY_NONZERO_VALUES")
        actual_var = _moment_variance(row["final_st_sum"],row["final_st_square_sum"],n)
        if m:
            var_ex = _moment_variance(row["paired_ex_sum"],row["paired_ex_square_sum"],m)
            var_fin = _moment_variance(row["paired_final_sum"],row["paired_final_square_sum"],m)
            cov = (row["paired_ex_final_product_sum"] / m
                   - (row["paired_ex_sum"] / m) * (row["paired_final_sum"] / m))
            if abs(cov) > math.sqrt(var_ex * var_fin) + 1e-8:
                raise ValueError("INCONSISTENT_ST_COVARIANCE")
        else:
            var_ex = var_fin = cov = None
        ex = exhibition[boat]
        if ex is not None and (type(ex) not in (int,float) or
                               not math.isfinite(ex) or not 0 <= ex <= 0.5):
            raise ValueError("INVALID_PRE_RESULT_EXHIBITION_ST")
        # With too few *paired* samples or no actual exhibition observation,
        # do NOT invent an ST measurement or a regression coefficient.
        beta = (m / (m + SHRINK_PAIRS) * cov / var_ex
                if m >= 20 and var_ex is not None and var_ex > 1e-10 else None)
        correction = (beta * (ex - row["paired_ex_sum"]/m)
                      if beta is not None and ex is not None else None)
        rows.append({
            "boat": boat,
            "training_n": n,
            "paired_n": m,
            "historical_actual_st_mean": row["final_st_sum"]/n if n else None,
            "historical_actual_st_sd": math.sqrt(actual_var) if actual_var is not None else None,
            "historical_top_start_count": top,
            "top_start_rate_shrunk_prior_one_sixth": (
                (top + TOP_RATE_PRIOR_N*TOP_RATE_PRIOR)/(n+TOP_RATE_PRIOR_N)
                if n else None),
            "observed_official_exhibition_st": ex,
            "regression_slope_shrunk_training_only": beta,
            "conditional_exhibition_st_correction_candidate": correction,
            "same_race_actual_st_observed": False,
            "features_imputed_from_absence": False,
        })
    return {
        "model_id": ID, "race_key": race_key, "research_only": True,
        "source_rights_and_timestamps_independently_verified_by_code": False,
        "original_commercial_provider_values_used": False,
        "historical_st_cutoff": scope["train_end"],
        "st_signals": rows,
        "top_start_rate_is_independent_per_boat_not_joint_race_probability": True,
        "exhibition_to_actual_st_is_unvalidated_research_correction": True,
        "actual_race_st_read": False, "formal_fresh_result_read": False,
        "improvement_proven": False, "production_eligible": False,
        "wager_eligible": False,
    }
