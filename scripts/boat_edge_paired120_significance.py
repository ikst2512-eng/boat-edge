"""Paired TopK significance for research-only independently admitted race pairs.

McNemar exact conditional two-sided p-value. This is a statistical comparison,
not proof the models were frozen, unseen, calibrated, or free of leakage.
"""
from __future__ import annotations
import math

TOPK = (1, 3, 5, 10)


def _outcomes(rows):
    outcomes = {}
    for rec in rows:
        ranks = [r["boat_combo"] for r in rec["ranked_120"]]
        actual = rec["actual_trifecta"]
        outcomes[rec["race_key"]] = ranks.index(actual)
    return outcomes


def exact_mcnemar(better, worse):
    discordant = better + worse
    if discordant == 0:
        return 1.0
    # Exact symmetric binomial test; recurrence starts at 2^-n.
    # lgamma avoids floating-point underflow for large n.
    small = min(better, worse)
    log_terms = [
        math.lgamma(discordant + 1) - math.lgamma(j + 1)
        - math.lgamma(discordant - j + 1) - discordant * math.log(2)
        for j in range(small + 1)
    ]
    maximum = max(log_terms)
    return min(1.0, 2.0 * math.exp(maximum) * math.fsum(
        math.exp(z - maximum) for z in log_terms))


def paired_significance(baseline_records, candidate_records):
    a = _outcomes(baseline_records)
    b = _outcomes(candidate_records)
    if not a or set(a) != set(b):
        raise ValueError("EXACT_SAME_NONEMPTY_PAIRED_RACES_REQUIRED")
    output = {}
    for k in TOPK:
        better = sum(b[key] < k <= a[key] for key in a)
        worse = sum(a[key] < k <= b[key] for key in a)
        output[str(k)] = {
            "candidate_only_hits": better,
            "baseline_only_hits": worse,
            "both_hit": sum(a[key] < k and b[key] < k for key in a),
            "both_miss": sum(a[key] >= k and b[key] >= k for key in a),
            "difference": (better - worse) / len(a),
            "mcnemar_exact_two_sided_p": exact_mcnemar(better, worse),
        }
    return {
        "paired_topk": output,
        "multiple_testing_note": "Four TopK hypotheses; unadjusted p-values, not adoption evidence",
        "statistical_significance_not_leakage_proof": True,
        "improvement_proven": False,
    }
