#!/usr/bin/env python3
"""V335 offline exploratory SITE-only paired outcome analysis.

Only loads *explicitly supplied*, postdeadline SITE-only outcome manifest.
Never discovers/fetches results, payouts, odds, formal data or combined APIs.
Requires immutable V332 predeadline research record, validates embedded
candidate/source digests, and an independent V232 saved baseline of same race.
Self-declared local predeadline times and outcome labels are NOT independent
evidence; even a positive exploratory comparison is NOT proof of improvement.
"""
from __future__ import annotations

import argparse
from datetime import datetime
import hashlib
import json
import math
from pathlib import Path

from boat_edge_v314_three_source_evidence import KEY, PROVIDERS, SHA
from boat_edge_v318_shadow_freeze import JST, canonical, parse_time
from boat_edge_v319_pre_result_pair import valid_tickets
from boat_edge_v320_site_v232_baseline_adapter import baseline_from_v232

MODEL = "BOAT_EDGE_V335_SITE_ONLY_EXPLORATORY_PAIRED_COMPARISON"
SCOPE = "SITE_ONLY_EXPLICITLY_SUPPLIED_POSTDEADLINE_OUTCOMES"
MEASURES = ("head_top1", "trifecta_top1", "trifecta_top3",
            "trifecta_top5", "trifecta_top10")


def _validate_frozen(shadow):
    if not isinstance(shadow, dict) or shadow.get("model_id") != "BOAT_EDGE_V332_LIVE_LOCAL_SHA_RESEARCH_ONLY":
        raise ValueError("V332_FROZEN_RESEARCH_REQUIRED")
    key = shadow.get("race_key")
    if not isinstance(key, str) or KEY.fullmatch(key) is None or key.startswith("20261001-"):
        raise ValueError("NONFORMAL_RACE_KEY_REQUIRED")
    deadline = parse_time(shadow.get("deadline_jst"))
    frozen = parse_time(shadow.get("frozen_at_jst"))
    if deadline.strftime("%Y%m%d") != key[:8] or frozen >= deadline:
        raise ValueError("PREDEADLINE_FREEZE_REQUIRED")
    if shadow.get("evidence_level") != "LOCAL_RECEIPT_RAW_SHA_ONLY":
        raise ValueError("LOCAL_SHA_EVIDENCE_REQUIRED")
    for flag in ("results_read", "formal_fresh_read", "accuracy_improvement_proven",
                 "model_promotion_authorized", "production_eligible",
                 "scoring_authorized", "wagers_authorized"):
        if shadow.get(flag) is not False:
            raise ValueError("RESEARCH_ONLY_GUARD_REQUIRED:" + flag)
    candidate = shadow.get("candidate")
    receipts = shadow.get("source_receipts")
    if not isinstance(candidate, dict) or not isinstance(receipts, dict):
        raise ValueError("FROZEN_CONTENT_MISSING")
    if set(receipts) != set(PROVIDERS):
        raise ValueError("THREE_SOURCE_RECEIPTS_REQUIRED")
    if hashlib.sha256(canonical(candidate)).hexdigest() != shadow.get("candidate_sha256"):
        raise ValueError("FROZEN_CANDIDATE_SHA_MISMATCH")
    if hashlib.sha256(canonical(receipts)).hexdigest() != shadow.get("source_bundle_sha256"):
        raise ValueError("FROZEN_SOURCE_RECEIPT_SHA_MISMATCH")
    # Canonical hashes prove internal consistency, not that the complete,
    # predeclared V312 ablation contract was retained after observation.
    if candidate.get("model_id") != "BOAT_EDGE_V312_UNCALIBRATED_EXHIBITION_ENTRY_ABLATION":
        raise ValueError("UNEXPECTED_CANDIDATE_MODEL")
    if candidate.get("deadline_jst") != deadline.isoformat():
        raise ValueError("CANDIDATE_DEADLINE_MISMATCH")
    if shadow.get("entry_basis") != "START_EXHIBITION_PROVISIONAL_NOT_ACTUAL":
        raise ValueError("FROZEN_ENTRY_BASIS_MISMATCH")
    if (candidate.get("race_key") != key or
            candidate.get("race_source_sha256") != shadow.get("race_source_sha256") or
            candidate.get("entry_basis") != "START_EXHIBITION_PROVISIONAL_NOT_ACTUAL"):
        raise ValueError("CANDIDATE_IDENTITY_OR_ENTRY_MISMATCH")
    if (candidate.get("scoring_authorized") is not False
            or candidate.get("improvement_proven") is not False
            or candidate.get("production_eligible") is not False):
        raise ValueError("CANDIDATE_GUARD_REQUIRED")
    if not isinstance(shadow.get("race_source_sha256"), str) or SHA.fullmatch(shadow["race_source_sha256"]) is None:
        raise ValueError("RACE_SOURCE_DIGEST_INVALID")
    modes = candidate.get("modes")
    if not isinstance(modes, dict) or set(modes) != {
            "national_only", "national_motor", "national_motor_st",
    }:
        raise ValueError("THREE_PREDECLARED_RESEARCH_MODES_REQUIRED")
    for name, row in modes.items():
        if not isinstance(name, str) or not isinstance(row, dict):
            raise ValueError("INVALID_RESEARCH_MODE")
        tickets = row.get("top10_boat_research_only")
        if not isinstance(tickets, list) or any(not isinstance(t, str) for t in tickets):
            raise ValueError("INVALID_RESEARCH_TICKETS")
        valid_tickets(tickets)
        heads = row.get("head_mass_boat_research_only")
        if not isinstance(heads, dict) or set(heads) != {str(x) for x in range(1, 7)}:
            raise ValueError("SIX_BOAT_HEAD_MASS_REQUIRED")
        values = list(heads.values())
        if (any(type(x) not in (int, float) or not math.isfinite(x) or x < 0
                for x in values) or not math.isclose(sum(values), 1.0, abs_tol=1e-7)):
            raise ValueError("INVALID_HEAD_MASS")
    return key, deadline, modes


def _measures(top10, head, outcome):
    if not isinstance(top10, list) or any(not isinstance(t, str) for t in top10):
        raise ValueError("INVALID_TICKETS")
    valid_tickets(top10)
    ticket = "-".join(str(v) for v in outcome[:3])
    return {
        "head_top1": int(int(head) == outcome[0]),
        "trifecta_top1": int(ticket in top10[:1]),
        "trifecta_top3": int(ticket in top10[:3]),
        "trifecta_top5": int(ticket in top10[:5]),
        "trifecta_top10": int(ticket in top10),
    }


def score_one(frozen, raw_baseline, outcome):
    """Pure exploratory comparison; never an authorized Formal Fresh scorer."""
    key, deadline, modes = _validate_frozen(frozen)
    base = baseline_from_v232(raw_baseline)
    if base["race_key"] != key or base["deadline_jst"] != deadline.isoformat():
        raise ValueError("BASELINE_RACE_OR_DEADLINE_MISMATCH")
    if not isinstance(outcome, dict) or outcome.get("race_key") != key:
        raise ValueError("OUTCOME_RACE_MISMATCH")
    finished = outcome.get("finish_order_boat")
    if (not isinstance(finished, list) or len(finished) != 6
            or any(type(v) is not int for v in finished)
            or set(finished) != set(range(1, 7))):
        raise ValueError("SIX_REAL_BOAT_FINISH_ORDER_REQUIRED")
    reported_at = parse_time(outcome.get("observed_at_jst"))
    if reported_at <= deadline:
        raise ValueError("POSTDEADLINE_OBSERVATION_REQUIRED")
    base_tickets = base["top10_boat"]
    baseline_measures = _measures(base_tickets, base_tickets[0].split("-")[0], finished)
    scored = {}
    for name, mode in sorted(modes.items()):
        heads = mode["head_mass_boat_research_only"]
        head = max(sorted(heads), key=lambda number: heads[number])
        scored[name] = _measures(mode["top10_boat_research_only"], head, finished)
    return {
        "race_key": key,
        "outcome_is_user_supplied_not_independently_verified": True,
        "baseline_model_id": base["model_id"],
        "baseline": baseline_measures,
        "candidate_modes": scored,
        "original_exhibition_verified": False,
        "independently_verified_actual_entry": False,
        "formal_fresh_read": False,
        "accuracy_improvement_proven": False,
    }


def _two_sided_sign_pvalue(candidate_only, baseline_only):
    n = candidate_only + baseline_only
    if n == 0:
        return None
    minority = min(candidate_only, baseline_only)
    return min(1.0, 2 * sum(math.comb(n, i) for i in range(minority + 1)) / (2 ** n))


def summarize(rows):
    if not rows:
        return {}
    names = set(rows[0]["candidate_modes"])
    if any(set(row["candidate_modes"]) != names for row in rows):
        raise ValueError("INCONSISTENT_MODEL_ABLATION_MODES")
    n = len(rows)
    baseline = {metric: sum(r["baseline"][metric] for r in rows) for metric in MEASURES}
    model_modes = {}
    for name in sorted(names):
        counts = {metric: sum(r["candidate_modes"][name][metric] for r in rows) for metric in MEASURES}
        pair_stats = {}
        for metric in MEASURES:
            b = sum(1 for r in rows
                    if r["candidate_modes"][name][metric] and not r["baseline"][metric])
            c = sum(1 for r in rows
                    if r["baseline"][metric] and not r["candidate_modes"][name][metric])
            pair_stats[metric] = {
                "candidate_only_hits": b, "baseline_only_hits": c,
                "exploratory_two_sided_sign_pvalue": _two_sided_sign_pvalue(b, c),
            }
        model_modes[name] = {
            "hits": counts, "hit_rates": {k: v / n for k, v in counts.items()},
            "delta_hit_rate_vs_baseline": {k: (v - baseline[k]) / n for k, v in counts.items()},
            "paired_discordance": pair_stats,
        }
    return {
        "races": n,
        "baseline_hits": baseline,
        "baseline_hit_rates": {k: v / n for k, v in baseline.items()},
        "candidate_modes": model_modes,
        "numbers_are_exploratory_not_production_evidence": True,
    }


def evaluate(root, manifest):
    if not isinstance(manifest, dict) or manifest.get("scope") != SCOPE:
        raise ValueError("EXPLICIT_SITE_ONLY_OUTCOME_SCOPE_REQUIRED")
    date = manifest.get("date")
    if not isinstance(date, str) or len(date) != 8 or not date.isdigit() or date == "20261001":
        raise ValueError("INVALID_OR_FORMAL_DATE")
    rows = manifest.get("outcomes")
    if not isinstance(rows, list):
        raise ValueError("OUTCOME_LIST_REQUIRED")
    root = Path(root).resolve()
    scored, rejected, seen = [], [], set()
    for outcome in rows:
        key = outcome.get("race_key") if isinstance(outcome, dict) else None
        if (not isinstance(key, str) or KEY.fullmatch(key) is None
                or key[:8] != date or key in seen):
            rejected.append({"race_key": key, "reason": "INVALID_DUPLICATE_OR_DIFFERENT_DATE"})
            continue
        seen.add(key)
        try:
            freeze_file = root / "data/research_local_v332" / date / (key + ".json")
            baseline_file = root / "data/site_autopilot/v232_cohort" / (key + ".json")
            if freeze_file.is_symlink() or baseline_file.is_symlink():
                raise ValueError("SYMLINK_SOURCE_FORBIDDEN")
            frozen = json.loads(freeze_file.read_text(encoding="utf-8"))
            baseline = json.loads(baseline_file.read_text(encoding="utf-8"))
            scored.append(score_one(frozen, baseline, outcome))
        except (OSError, ValueError, UnicodeError, TypeError, KeyError) as exc:
            rejected.append({"race_key": key, "reason": str(exc)})
    return {
        "model_id": MODEL, "scope": SCOPE, "date": date,
        "supplied_outcome_rows": len(rows), "paired_evaluated": len(scored),
        "rejected": rejected, "exploratory_metrics": summarize(scored),
        "per_race": scored,
        "independently_verified_capture_time": False,
        "outcomes_independently_verified": False,
        "formal_fresh_read": False, "formal_scoring_performed": False,
        "accuracy_improvement_proven": False,
        "model_promotion_authorized": False, "wagers_authorized": False,
    }


def main():
    parser = argparse.ArgumentParser(description="Only explicitly supplied SITE outcomes; no result fetching")
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--outcome-manifest", required=True, type=Path)
    args = parser.parse_args()
    manifest = json.loads(args.outcome_manifest.read_text(encoding="utf-8"))
    print(json.dumps(evaluate(args.root, manifest), ensure_ascii=False, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
