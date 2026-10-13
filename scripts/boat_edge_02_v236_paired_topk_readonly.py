#!/usr/bin/env python3
"""Read-only, site-only paired Top3/5/10 evaluation of already scored V236 races.

Never reads formal Fresh, raw outcomes, or unscored race data. Does not promote.
"""
import argparse
import json
from pathlib import Path

MODES = ("hit10", "balance10", "scenario7plus3")
TOPK = (3, 5, 10)

def evaluate(root: Path):
    base = root / "data/site_autopilot"
    scores = base / "v236_scored"
    frozen = base / "v236_frozen"
    totals = {m: {str(k): {"hits": 0, "gain": 0, "loss": 0} for k in TOPK} for m in MODES}
    exclusions = {}
    included = 0
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
            if not isinstance(winner, str) or len(winner.split("-")) != 3:
                raise ValueError("winner_invalid")
            if any(not isinstance(tickets.get(m), list) or len(tickets[m]) != 10
                   or len(set(tickets[m])) != 10 for m in MODES):
                raise ValueError("tickets_invalid")
            if any(bool(s["outcomes"][m]) != (winner in tickets[m]) for m in MODES):
                raise ValueError("score_parity")
            included += 1
            for k in TOPK:
                reference = winner in tickets["hit10"][:k]
                for m in MODES:
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
    return {"scope": "POST_RESULT_SITE_ONLY_NOT_FORMAL_FRESH",
            "source": "v236_scored_plus_original_v236_frozen",
            "races": included, "excluded": exclusions, "topk": totals,
            "promotion_authorized": False, "production_model_changed": False,
            "note": "Descriptive paired comparison; no statistical promotion or formal Fresh claim."}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("."))
    args = parser.parse_args()
    print(json.dumps(evaluate(args.root), ensure_ascii=False, sort_keys=True, indent=2))

if __name__ == "__main__":
    main()
