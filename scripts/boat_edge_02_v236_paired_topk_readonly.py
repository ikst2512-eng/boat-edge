#!/usr/bin/env python3
"""Read-only, site-only paired Top3/5/10 evaluation of already scored V236 races.

Never reads formal Fresh, raw outcomes, or unscored race data. Does not promote.
"""
import argparse
from collections import Counter
import hashlib
import json
import math
import re
from datetime import datetime
from pathlib import Path

MODES = ("hit10", "balance10", "scenario7plus3")
TOPK = (3, 5, 10)
COMBO = re.compile(r"^[1-6]-[1-6]-[1-6]$")


def valid_combo(value):
    return isinstance(value, str) and COMBO.fullmatch(value) is not None and len(set(value.split("-"))) == 3


def timestamp(value):
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("naive_timestamp")
    return parsed


def cause(tickets, winner):
    if winner in tickets:
        return "hit"
    head, second, _ = winner.split("-")
    if not any(x.split("-")[0] == head for x in tickets):
        return "head_absent"
    if not any(x.startswith(head + "-" + second + "-") for x in tickets):
        return "second_absent_given_head"
    return "third_absent_given_head_second"

def rank_head_diversified(hit10, k, keep):
    """Post-hoc hypothesis, NOT a predeadline frozen prediction.

    Preserve `keep` original highest-ranked tickets, then give non-primary
    heads priority for remaining slots before filling by original rank.
    This heuristic never uses the race result to construct tickets.
    """
    seed = hit10[:keep]
    alt = [t for t in hit10 if t[0] != hit10[0][0] and t not in seed]
    fallback = [t for t in hit10 if t not in seed]
    return list(dict.fromkeys(seed + alt + fallback))[:k]


def require_formal_closed(root: Path):
    """No outcome-bearing SITE read unless the dynamic Formal cohort is empty/locked."""
    try:
        status = json.loads((root / "data/formal_status.json").read_text(encoding="utf-8"))
        guards = status["guards"]
        cohort = status["formalFirst100"]
        valid = (
            isinstance(guards, dict) and isinstance(cohort, dict)
            and all(guards.get(k) is False for k in ("results_seen", "unlock", "scoring"))
            and guards.get("RESULT_UNLOCK_TOKEN", "NOT_DECLARED") is None
            and type(cohort.get("races")) is int and cohort["races"] == 0
        )
    except (OSError, ValueError, TypeError, KeyError):
        valid = False
    if not valid:
        raise RuntimeError("SITE_ONLY_PAIRED_FORMAL_GATE_CLOSED_EMPTY_REQUIRED")


def paired_exact_p(gain, loss):
    """Two-sided exact discordant-pair sign test; descriptive, not promotion."""
    n = gain + loss
    if not n:
        return None
    tail = sum(math.comb(n, j) for j in range(min(gain, loss) + 1))
    return round(min(1.0, 2 * tail / (2 ** n)), 12)


def evaluate(root: Path):
    require_formal_closed(root)
    base = root / "data/site_autopilot"
    scores = base / "v236_scored"
    frozen = base / "v236_frozen"
    totals = {m: {str(k): {"hits": 0, "gain": 0, "loss": 0} for k in TOPK} for m in MODES}
    exclusions = {}
    included = 0
    baseline_rank_buckets = Counter()
    baseline_failure_by_k = {str(k): Counter() for k in TOPK}
    prefix_identical = {m: {str(k): True for k in TOPK} for m in MODES if m != "hit10"}
    per_day = {}
    exploratory = {"head_diversified3": {"k": 3, "keep": 2, "hits": 0, "gain": 0, "loss": 0, "changed": 0},
                   "head_diversified5": {"k": 5, "keep": 3, "hits": 0, "gain": 0, "loss": 0, "changed": 0}}
    for p in sorted(scores.glob("20??????-??-??.json")):
        try:
            s = json.loads(p.read_text(encoding="utf-8"))
            f = json.loads((frozen / p.name).read_text(encoding="utf-8"))
            if (s.get("schema") != "BOAT_EDGE_V236_HITRATE_SCORE_V1"
                    or s.get("scope") != "POST_RESULT_SITE_ONLY_NOT_FORMAL_FRESH"
                    or f.get("schema") != "BOAT_EDGE_V236_HITRATE_FORWARD_SHADOW_V1"
                    or not (s.get("race_key") == f.get("race_key") == p.stem)):
                raise ValueError("schema_or_identity")
            winner = s["official_result"]
            tickets = f["comparators"]
            if not valid_combo(winner):
                raise ValueError("winner_invalid")
            if any(not isinstance(tickets.get(m), list) or len(tickets[m]) != 10
                   or len(set(tickets[m])) != 10
                   or not all(valid_combo(t) for t in tickets[m]) for m in MODES):
                raise ValueError("tickets_invalid")
            if (f.get("result_seen_at_freeze") is not False
                    or f.get("production_model_changed") is not False
                    or s.get("model_promotion_authorized") is not False
                    or s.get("production_accuracy_improvement_proven") is not False
                    or any(type(s["outcomes"][m]) is not bool for m in MODES)
                    or any(s["outcomes"][m] != (winner in tickets[m]) for m in MODES)):
                raise ValueError("scope_or_score_parity")
            if not (timestamp(f["frozen_at"]) < timestamp(f["deadline_jst"])
                    and timestamp(f["v232_first_git_committed_at"]) < timestamp(f["deadline_jst"])):
                raise ValueError("deadline_parity")
            if s.get("frozen_candidate_sha256") != hashlib.sha256((frozen / p.name).read_bytes()).hexdigest():
                raise ValueError("frozen_digest_mismatch")
            included += 1
            rank = (tickets["hit10"].index(winner) + 1
                    if winner in tickets["hit10"] else None)
            bucket = ("rank1_3" if rank is not None and rank <= 3 else
                      "rank4_5" if rank is not None and rank <= 5 else
                      "rank6_10" if rank is not None else "outside_top10")
            baseline_rank_buckets[bucket] += 1
            for name, e in exploratory.items():
                k = e["k"]
                candidate = rank_head_diversified(tickets["hit10"], k, e["keep"])
                baseline_hit = winner in tickets["hit10"][:k]
                candidate_hit = winner in candidate
                e["hits"] += int(candidate_hit)
                e["gain"] += int(candidate_hit and not baseline_hit)
                e["loss"] += int(baseline_hit and not candidate_hit)
                e["changed"] += int(candidate != tickets["hit10"][:k])
            day = p.stem[:8]
            if day not in per_day:
                per_day[day] = {m: {str(k): 0 for k in TOPK} for m in MODES}
                per_day[day]["races"] = 0
            per_day[day]["races"] += 1
            for k in TOPK:
                reference = winner in tickets["hit10"][:k]
                baseline_failure_by_k[str(k)][cause(tickets["hit10"][:k], winner)] += 1
                for m in MODES:
                    if m != "hit10" and tickets[m][:k] != tickets["hit10"][:k]:
                        prefix_identical[m][str(k)] = False
                    per_day[day][m][str(k)] += int(winner in tickets[m][:k])
                    hit = winner in tickets[m][:k]
                    row = totals[m][str(k)]
                    row["hits"] += int(hit)
                    row["gain"] += int(hit and not reference)
                    row["loss"] += int(reference and not hit)
        except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError) as e:
            reason = str(e) if isinstance(e, ValueError) else type(e).__name__
            exclusions[reason] = exclusions.get(reason, 0) + 1
    for mode in MODES:
        for k in TOPK:
            row = totals[mode][str(k)]
            row["races"] = included
            row["hit_rate_percent"] = round(100 * row["hits"] / included, 2) if included else None
            row["net_gain"] = row["gain"] - row["loss"]
            row["discordant_pairs"] = row["gain"] + row["loss"]
            row["paired_exact_p_two_sided"] = paired_exact_p(row["gain"], row["loss"])
    for row in exploratory.values():
        row["races"] = included
        row["hit_rate_percent"] = round(100 * row["hits"] / included, 2) if included else None
        row["net_gain"] = row["gain"] - row["loss"]
    return {"scope": "POST_RESULT_SITE_ONLY_NOT_FORMAL_FRESH",
            "source": "v236_scored_plus_original_v236_frozen",
            "races": included, "excluded": exclusions, "topk": totals,
            "post_hoc_exploration_not_predeadline_evidence": {
                "status": "HYPOTHESIS_ONLY_NO_PROSPECTIVE_CANDIDATE_FREEZE",
                "construction": "ORIGINAL_TOP10_RANK_ONLY_MOVE_OTHER_HEADS_FORWARD",
                "candidates": exploratory,
                "promotion_authorized": False,
            },
            "diagnostics": {
                "baseline_rank_buckets": dict(sorted(baseline_rank_buckets.items())),
                "baseline_failure_by_k": {k: dict(sorted(v.items())) for k, v in baseline_failure_by_k.items()},
                "identical_frozen_prefix_vs_baseline": prefix_identical,
                "per_day": dict(sorted(per_day.items())),
            },
            "promotion_authorized": False, "production_model_changed": False,
            "note": "Descriptive paired comparison only. Exact paired p is not a multi-day untouched Fresh acceptance or proof of model improvement."}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("."))
    args = parser.parse_args()
    print(json.dumps(evaluate(args.root), ensure_ascii=False, sort_keys=True, indent=2))

if __name__ == "__main__":
    main()
