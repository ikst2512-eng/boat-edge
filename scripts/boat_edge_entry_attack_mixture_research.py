"""Research-only entry/attack scenario mixture for all 120 boat-number trifectas.

Scenario weights are externally specified hypotheses, NOT fitted or calibrated
win probabilities. No historical reconstruction, results, wagers or Formal Fresh.
"""
from __future__ import annotations
import itertools
import math

BOATS = frozenset(range(1, 7))
ATTACKS = ("escape", "sashi", "makuri", "makuri_sashi", "follow", "other")
MODEL = "BOAT_EDGE_ENTRY_ATTACK_MIXTURE_RESEARCH_V1"


def _permutation(entry):
    if not isinstance(entry, dict) or set(entry) != BOATS or any(type(x) is not int for x in entry.values()) or set(entry.values()) != BOATS:
        raise ValueError("SIX_BOAT_ENTRY_PERMUTATION_REQUIRED")


def rank_scenarios(scenarios):
    """Each scenario: entry {boat:course}, attacker (boat), attack, weight, strengths {boat:positive}.

    Mixture components explicitly condition on entry AND attacker/method. The
    attack's influence on strengths is supplied by the upstream hypothesis;
    this module never silently invents attack-effect coefficients.
    """
    if not isinstance(scenarios, list) or not scenarios:
        raise ValueError("SCENARIOS_REQUIRED")
    mass = {triple: 0.0 for triple in itertools.permutations(range(1, 7), 3)}
    total_weight = 0.0
    coverage = set()
    for sc in scenarios:
        if not isinstance(sc, dict) or set(sc) != {"entry", "attacker", "attack", "weight", "strengths"}:
            raise ValueError("SCENARIO_FIELDS_INVALID")
        entry, attacker, attack = sc["entry"], sc["attacker"], sc["attack"]
        _permutation(entry)
        if type(attacker) is not int or attacker not in BOATS or attack not in ATTACKS:
            raise ValueError("ATTACK_INVALID")
        strengths = sc["strengths"]
        if not isinstance(strengths, dict) or set(strengths) != BOATS or any(
            type(v) not in (int, float) or not math.isfinite(v) or v <= 0 for v in strengths.values()
        ):
            raise ValueError("STRENGTHS_INVALID")
        weight = sc["weight"]
        if type(weight) not in (int, float) or not math.isfinite(weight) or weight <= 0:
            raise ValueError("SCENARIO_WEIGHT_INVALID")
        # Divide by max to avoid overflow in sum and sequential PL terms.
        mx = max(strengths.values())
        w = {boat: strengths[boat] / mx for boat in BOATS}
        denom = math.fsum(w.values())
        for a, b, c in mass:
            pa = w[a] / denom
            pb = w[b] / (denom - w[a])
            pc = w[c] / (denom - w[a] - w[b])
            mass[a, b, c] += weight * pa * pb * pc
        total_weight += weight
        coverage.add((entry[attacker], attack))
    if not math.isfinite(total_weight) or total_weight <= 0:
        raise ValueError("TOTAL_WEIGHT_INVALID")
    total_mass = math.fsum(mass.values())
    if not math.isfinite(total_mass) or total_mass <= 0:
        raise ValueError("TOTAL_MASS_INVALID")
    rows = [{"boat_combo": "-".join(map(str, key)), "relative_model_mass": value / total_mass}
            for key, value in mass.items()]
    rows.sort(key=lambda r: (-r["relative_model_mass"], r["boat_combo"]))
    if len(rows) != 120 or len({r["boat_combo"] for r in rows}) != 120 or not math.isclose(
        math.fsum(r["relative_model_mass"] for r in rows), 1.0, abs_tol=1e-12
    ):
        raise AssertionError("INVALID_RANKED_120")
    return {"model_id": MODEL, "research_only": True, "calibrated": False,
            "improvement_proven": False, "production_eligible": False,
            "formal_fresh_eligible": False, "wagers_authorized": False,
            "entry_attack_coverage": [{"course": c, "attack": a} for c, a in sorted(coverage)],
            "coverage_complete": len(coverage) == 6 * len(ATTACKS),
            "ranked_120": rows}
