"""Research-only training-count hierarchical conditional 120-way ranker.

Inputs MUST be independently authorized, training-only aggregated counts. This
module does not fetch data, extract results, learn from a target race, access
formal Fresh, place wagers, or modify production predictions. Its 120-way
relative masses are NOT calibrated race probabilities.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
import math
import re

MODEL = "BOAT_EDGE_02_HIERARCHICAL_CONDITIONAL_RESEARCH_V1"
BOATS = tuple(range(1, 7))
LAYERS = ("national", "venue", "racer", "motor")
# Fixed protocol; changes require a separate version and predeclared trial.
PRIOR_STRENGTH = {"national": 12.0, "venue": 32.0, "racer": 48.0, "motor": 64.0}
RACE = re.compile(r"20\d{6}-\d{2}-\d{2}\Z")
SHA = re.compile(r"[0-9a-f]{64}\Z")
# Conservative known Formal/diagnostic research-protected cohort dates.
# Caller must ALSO check the current dynamic Formal protected date set;
# this static gate is not an exhaustive permission to access historical outcomes.
RESEARCH_PROTECTED_DATES = frozenset(("20261001", "20261005", "20261013"))


def _date(value):
    if not isinstance(value, str) or not re.fullmatch(r"20\d{6}", value):
        raise ValueError("BAD_EVIDENCE_DATE")
    try:
        return date(int(value[:4]), int(value[4:6]), int(value[6:8]))
    except ValueError as exc:
        raise ValueError("BAD_EVIDENCE_DATE") from exc


def _check_scope(scope, race_key):
    if not isinstance(race_key, str) or RACE.fullmatch(race_key) is None:
        raise ValueError("INVALID_RACE_KEY")
    if race_key[:8] in RESEARCH_PROTECTED_DATES:
        raise ValueError("FORMAL_FRESH_EXCLUDED")
    if not isinstance(scope, dict) or set(scope) != {
        "schema", "race_key", "train_end", "first_frozen_at", "deadline_jst",
        "authorized_training_aggregate", "reviewed_permission_evidence_sha256",
        "source_manifest_sha256", "source_class", "no_target_outcome",
        "formal_fresh_not_used",
    }:
        raise ValueError("EXPLICIT_SOURCE_AND_TIME_SCOPE_REQUIRED")
    if scope["schema"] != "BE02_RESEARCH_AGGREGATE_SCOPE_V1" or scope["race_key"] != race_key:
        raise ValueError("SCOPE_RACE_MISMATCH")
    if scope["source_class"] != "REVIEWED_AUTHORIZED_OFFICIAL_DERIVED_AGGREGATES":
        raise ValueError("UNAUTHORIZED_OR_UNREVIEWED_SOURCE")
    if (scope["authorized_training_aggregate"] is not True or
            scope["no_target_outcome"] is not True or
            scope["formal_fresh_not_used"] is not True):
        raise ValueError("PRE_RESULT_RESEARCH_GUARDS_REQUIRED")
    if any(not isinstance(scope[k], str) or SHA.fullmatch(scope[k]) is None for k in (
        "reviewed_permission_evidence_sha256", "source_manifest_sha256")):
        raise ValueError("PROVENANCE_DIGESTS_REQUIRED")
    race_day = _date(race_key[:8])
    train_end = _date(scope["train_end"])
    if train_end >= race_day:
        raise ValueError("TRAINING_NOT_EARLIER_THAN_TARGET")
    try:
        freeze = datetime.fromisoformat(scope["first_frozen_at"])
        due = datetime.strptime(race_key[:8] + scope["deadline_jst"], "%Y%m%d%H:%M").replace(
            tzinfo=timezone(timedelta(hours=9)))
    except (TypeError, ValueError) as exc:
        raise ValueError("INVALID_FIRST_FREEZE_TIME_OR_DEADLINE") from exc
    if (freeze.tzinfo is None or freeze.utcoffset() != timedelta(hours=9)
            or freeze.date() != race_day or not freeze < due):
        raise ValueError("INVALID_FIRST_FREEZE_TIME_OR_DEADLINE")
    # This metadata check is NOT independent proof of the first freeze time.
    return scope


def _posterior(groups, labels):
    """Sequential Dirichlet shrinkage; missing layers stay absent, never zero-imputed."""
    if not isinstance(groups, dict) or set(groups) != set(LAYERS):
        raise ValueError("ALL_LAYER_KEYS_REQUIRED")
    prior = {key: 1.0 / len(labels) for key in labels}
    used = []
    for layer in LAYERS:
        counts = groups[layer]
        if counts is None:
            continue
        if not isinstance(counts, dict) or set(counts) != set(labels):
            raise ValueError("BAD_LAYER_COUNT_LABELS:" + layer)
        if any(type(v) is not int or v < 0 for v in counts.values()):
            raise ValueError("INVALID_LAYER_COUNTS:" + layer)
        n = sum(counts.values())
        if n == 0:
            continue
        alpha = PRIOR_STRENGTH[layer]
        prior = {k: (counts[k] + alpha * prior[k]) / (n + alpha) for k in labels}
        used.append(layer)
    if not used:
        raise ValueError("NO_OBSERVED_AUTHORIZED_COUNTS")
    return prior, used


def rank_120(race_key, scope, count_groups):
    """Scores P(head)*P(second|head)*P(third|head,second) from provided counts."""
    _check_scope(scope, race_key)
    if not isinstance(count_groups, dict) or set(count_groups) != {"head", "second", "third"}:
        raise ValueError("ALL_CONDITIONAL_STAGES_REQUIRED")
    head, use_h = _posterior(count_groups["head"], BOATS)
    if not isinstance(count_groups["second"], dict) or set(count_groups["second"]) != set(BOATS):
        raise ValueError("ALL_HEAD_CONDITIONALS_REQUIRED")
    if not isinstance(count_groups["third"], dict) or set(count_groups["third"]) != {
        (h, s) for h in BOATS for s in BOATS if s != h
    }:
        raise ValueError("ALL_PAIR_CONDITIONALS_REQUIRED")
    scores = []
    seen_layers = {"head": use_h, "second": {}, "third": {}}
    for h in BOATS:
        seconds = tuple(x for x in BOATS if x != h)
        sec_probs, used = _posterior(count_groups["second"][h], seconds)
        seen_layers["second"][str(h)] = used
        for s in seconds:
            thirds = tuple(x for x in BOATS if x not in (h, s))
            third_probs, used = _posterior(count_groups["third"][(h, s)], thirds)
            seen_layers["third"][f"{h}-{s}"] = used
            for t in thirds:
                scores.append((f"{h}-{s}-{t}", head[h] * sec_probs[s] * third_probs[t]))
    total = sum(p for _, p in scores)
    if len(scores) != 120 or len({k for k, _ in scores}) != 120 or not math.isclose(total, 1, abs_tol=1e-12):
        raise ValueError("CONDITIONAL_120_INVALID")
    rows = sorted(scores, key=lambda r: (-r[1], r[0]))
    return {
        "model_id": MODEL, "race_key": race_key,
        "research_only": True, "calibrated": False, "accuracy_improvement_proven": False,
        "formal_fresh_read": False, "results_read": False, "production_eligible": False,
        "wagers_authorized": False, "source_scope_self_reported_not_authenticated": True,
        "used_layers": seen_layers,
        "ranked_120": [{"boat_combo": k, "relative_model_mass": p} for k, p in rows],
        "top10_boat_research_only": [k for k, _ in rows[:10]],
        "head_mass_boat": {str(h): head[h] for h in BOATS},
    }
