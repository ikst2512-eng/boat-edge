#!/usr/bin/env python3
"""Read-only Top3/5/10 audit of V301-verified SITE-only scored records.

Never reads Formal Fresh results, results endpoints or payout APIs.
"""
import argparse
import json
from pathlib import Path
from scripts.boat_edge_v301_paired_evidence import BASE, CONFIG, EvidenceError, checked_row, formal_lock, read, combo
from scripts.boat_edge_v241_results import build as verified_v241_build
from scripts.boat_edge_v305_site_miss_attribution import category as existing_v305_category

def ranked_site_baseline_by_day(normalized):
    """Descriptive, non-additive rank bins from *already validated* V241 rows.

    Caller must have applied V241 Git-original and V234 post-result guards.
    No candidate comparison, retro-ranking or model-selection inference.
    """
    by_day = {}
    rank_bins = ("top3", "rank4_5", "rank6_10", "outside_top10")
    for row in normalized:
        key, day = row["key"], row["day"]
        if day != key[:8] or not isinstance(row["baseline"], list) or len(row["baseline"]) != 10:
            raise EvidenceError("V235_INVALID_VALIDATED_DAY_OR_RANKING")
        if len(set(row["baseline"])) != 10 or any(not combo(x) for x in row["baseline"]):
            raise EvidenceError("V235_INVALID_VALIDATED_RANKING")
        win = row["winning"]
        if not combo(win):
            raise EvidenceError("V235_INVALID_VALIDATED_WINNER")
        d = by_day.setdefault(day, {
            "races": 0,
            "baseline_hits": {"3": 0, "5": 0, "10": 0},
            "rank_bins": {k: 0 for k in rank_bins},
            "miss_leg_partition": {k: 0 for k in (
                "top10_hit", "head_missing", "second_missing_given_head",
                "third_missing_given_head_second")},
        })
        d["races"] += 1
        position = row["baseline"].index(win) + 1 if win in row["baseline"] else None
        bin_name = ("outside_top10" if position is None else "top3" if position <= 3
                    else "rank4_5" if position <= 5 else "rank6_10")
        d["rank_bins"][bin_name] += 1
        for n in (3, 5, 10):
            d["baseline_hits"][str(n)] += (position is not None and position <= n)
        d["miss_leg_partition"][existing_v305_category(row)] += 1
    if sum(d["races"] for d in by_day.values()) != len(normalized):
        raise EvidenceError("V235_DAY_TOTAL_MISMATCH")
    for day, d in by_day.items():
        b = d["rank_bins"]
        hits = d["baseline_hits"]
        if (sum(b.values()) != d["races"]
                or hits != {"3": b["top3"], "5": b["top3"] + b["rank4_5"],
                            "10": b["top3"] + b["rank4_5"] + b["rank6_10"]}
                or sum(d["miss_leg_partition"].values()) != d["races"]
                or d["miss_leg_partition"]["top10_hit"] != hits["10"]):
            raise EvidenceError("V235_DAY_RANK_BUCKETS_INCONSISTENT_" + day)
    return {day: by_day[day] for day in sorted(by_day)}


def reconcile_v235_baseline(rows, original_cohorts, shadow_unique):
    """Pure reconciliation of V241-verified SITE rows; not a result scorer.

    Caller must first verify each row with existing V241.build (which attests
    original bytes, first Git commit, result timing and V234 score).
    """
    if not isinstance(rows, list) or not isinstance(original_cohorts, dict):
        raise EvidenceError("V235_V241_INVALID_INPUT")
    by_key = {}
    normalized = []
    for row in rows:
        if not isinstance(row, dict):
            raise EvidenceError("V235_V241_INVALID_ROW")
        key = row.get("race_key")
        if not isinstance(key, str) or not key.startswith("20") or key in by_key:
            raise EvidenceError("V235_V241_DUPLICATE_OR_INVALID_RACE")
        parent = original_cohorts.get(key)
        if (not isinstance(parent, dict) or parent.get("race_key") != key
                or parent.get("schema") != "BOAT_EDGE_V232_SITE_PROSPECTIVE_ACCURACY_COHORT_V1"
                or parent.get("scope") != "SITE_REFERENCE_UNSEEN_PRE_RESULT_ONLY_NOT_FORMAL_FRESH"
                or any(parent.get(k) is not False for k in
                       ("formal_results_seen", "formal_gate_unlocked",
                        "paper_purchases_authorized", "real_purchases_authorized"))):
            raise EvidenceError("V235_V232_ORIGINAL_COHORT_INVALID_" + key)
        top = parent.get("top10")
        if (not isinstance(top, list) or len(top) != 10 or len(set(top)) != 10
                or any(not combo(x) for x in top)
                or parent.get("top3") != top[:3] or parent.get("top5") != top[:5]):
            raise EvidenceError("V235_ORDERED_TOPK_NOT_FROZEN_" + key)
        hit = (parent.get("frozen_mode_tickets") or {}).get("hit")
        if (not isinstance(hit, list) or len(hit) != 10
                or any(not isinstance(x, dict) for x in hit)
                or [x.get("combo") for x in hit] != top):
            raise EvidenceError("V235_RANKED_HIT_TICKETS_MISMATCH_" + key)
        winning = row.get("winning_combo")
        if (not combo(winning) or row.get("model_id") != "SITE_REFERENCE_V122"
                or parent.get("model_id") != row.get("model_id")
                or row.get("date_jst") != key[:8]
                or row.get("head_prediction") != top[0].split("-")[0]
                or row.get("post_result_verified") is not True):
            raise EvidenceError("V235_MODEL_OR_RESULT_MISMATCH_" + key)
        expected = {"top3_hit": winning in top[:3], "top5_hit": winning in top[:5],
                    "top10_hit": winning in top}
        if any(row.get(field) is not value for field, value in expected.items()):
            raise EvidenceError("V235_REPORTED_TOPK_PARITY_MISMATCH_" + key)
        if key in shadow_unique:
            shadow = shadow_unique[key]
            if (shadow["winning"] != winning or shadow["baseline"] != top
                    or shadow["day"] != key[:8]):
                raise EvidenceError("V235_V301_OVERLAP_CONFLICT_" + key)
        normalized.append({"key": key, "day": key[:8],
                           "winning": winning, "baseline": top})
        by_key[key] = row
    if set(shadow_unique) - set(by_key):
        raise EvidenceError("V235_V301_SHADOW_ROW_NOT_IN_V241")
    counts = {k: 0 for k in ("top10_hit", "head_missing",
                            "second_missing_given_head", "third_missing_given_head_second")}
    for row in normalized:
        counts[existing_v305_category(row)] += 1
    if sum(counts.values()) != len(rows):
        raise EvidenceError("V235_V305_MISS_PARTITION_INVALID")
    return {"scope": "V241_GIT_VERIFIED_SITE_BASELINE_NOT_FORMAL_FRESH",
            "baseline": summarize(normalized),
            "miss_leg_partition": counts,
            "verified_baseline_by_day": ranked_site_baseline_by_day(normalized),
            "by_day_descriptive_only_not_evidence_of_model_improvement": True,
            "additional_unique_outside_v301": len(by_key) - len(shadow_unique),
            "v301_race_keys_all_contained": True,
            "candidate_top3_top5_delta": None,
            "prospective_candidate_improvement_proven": False,
            "promotion_authorized": False}


def audit(root):
    root = Path(root).resolve()
    formal_lock(root)
    studies = {}
    unique = {}
    for study in CONFIG:
        folder = root / BASE / (study + "_scored")
        if not folder.is_dir():
            raise EvidenceError("SCORED_COHORT_DIRECTORY_MISSING_" + study)
        rows = []
        for path in sorted(folder.glob("*.json")):
            row = checked_row(root, study, path)
            rows.append(row)
            key = row["key"]
            if key in unique and (unique[key]["baseline"] != row["baseline"] or unique[key]["winning"] != row["winning"]):
                raise EvidenceError("CROSS_STUDY_BASELINE_CONFLICT_" + key)
            unique[key] = row
        studies[study] = summarize(rows)
    # Reuse the existing V241 immutable Git-first and V234 score validator.
    # Never treat the V301 study union and the larger V235 baseline as additive.
    verified = verified_v241_build(root)
    if verified != read(root / BASE / "v241_results_current.json"):
        raise EvidenceError("V235_V241_PUBLISHED_SNAPSHOT_DRIFT")
    originals = {}
    for item in verified["rows"]:
        key = item["race_key"]
        if key in originals:
            raise EvidenceError("V235_V241_DUPLICATE_RACE_" + key)
        originals[key] = read(root / BASE / "v232_cohort" / (key + ".json"))
    v235_baseline = reconcile_v235_baseline(verified["rows"], originals, unique)
    return {"schema":"BOAT_EDGE_V304_SITE_ONLY_RANKED_TOPK_AUDIT_V1",
            "scope":"V301_GIT_VERIFIED_SCORED_SITE_ONLY_NOT_FORMAL_FRESH",
            "studies":studies,"unique_races":summarize(list(unique.values())),
            "v235_v234_v241_site_baseline":v235_baseline,
            "overlap_not_additive":True,"promotion_authorized":False,
            "accuracy_improvement_proven":False,"formal_results_read":False}

def summarize(rows):
    n = len(rows)
    hits = {str(k):sum(r["winning"] in r["baseline"][:k] for r in rows) for k in (3,5,10)}
    return {"races":n,"days":len({r["day"] for r in rows}),
            "baseline_hits":hits,
            "baseline_hit_rate":{k:(v/n if n else None) for k,v in hits.items()},
            "new_model_delta":None,
            "candidate_top3_top5_unavailable":True}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--root",default=".")
    args=p.parse_args()
    print(json.dumps(audit(args.root),sort_keys=True,indent=2))

if __name__=="__main__":
    main()
