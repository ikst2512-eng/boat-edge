#!/usr/bin/env python3
"""Read-only confidence audit of independently scored V234 SITE races.

This does not fetch outcomes, change formal Fresh or establish model superiority.
Wilson intervals quantify sampling uncertainty, not provenance uncertainty.
"""
from __future__ import annotations
import argparse
import json
import math
import re
from pathlib import Path

METRICS = ("head_hit", "top3_hit", "top5_hit", "top10_hit")
SCHEMA = "BOAT_EDGE_V234_PRECOMMITTED_SITE_ONLY_RESULT_SCORE_V1"
Z = 1.959963984540054
RACE_KEY = re.compile(r"^20[0-9]{6}-[0-9]{2}-[0-9]{2}$")
MAX_RECORD_BYTES = 20 * 1024


def wilson(hits: int, n: int):
    if n <= 0:
        return None
    p = hits / n
    z2 = Z * Z
    den = 1 + z2 / n
    center = (p + z2 / (2 * n)) / den
    margin = Z * math.sqrt((p * (1 - p) + z2 / (4 * n)) / n) / den
    return [max(0.0, center - margin), min(1.0, center + margin)]


def audit(root: Path):
    scored_dir = root / "data/site_autopilot/v234_scored"
    summary_path = root / "data/site_autopilot/v234_current.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    rows, errors = [], []
    for path in sorted(scored_dir.glob("*.json")):
        try:
            if not RACE_KEY.fullmatch(path.stem):
                raise ValueError("INVALID_RACE_KEY")
            if path.is_symlink() or not path.is_file():
                raise ValueError("UNSAFE_RECORD_FILE")
            if path.stat().st_size > MAX_RECORD_BYTES:
                raise ValueError("OVERSIZED_RECORD_FILE")
            row = json.loads(path.read_text(encoding="utf-8"))
            if (row.get("schema") != SCHEMA or row.get("race_key") != path.stem
                or row.get("scope") != "POST_RESULT_SITE_RESEARCH_ONLY_FORMAL_FRESH_LOCKED"
                or not all(type(row.get(m)) is bool for m in METRICS)
                or not (row["top3_hit"] <= row["top5_hit"] <= row["top10_hit"])
                or row.get("accuracy_improvement_proven") is not False
                or row.get("model_promotion_authorized") is not False
                or not row.get("first_git_commit") or not row.get("cohort_sha256")
                or not row.get("result_sha256")):
                raise ValueError("INVALID_SCORED_EVIDENCE")
            rows.append(row)
        except (OSError, ValueError, TypeError) as exc:
            errors.append({"race_key": path.stem, "reason": str(exc)})
    counts = {m: sum(row[m] for row in rows) for m in METRICS}
    n = len(rows)
    reported = {"head_hit": "head_hit", "top3_hit": "top3_hit",
                "top5_hit": "top5_hit", "top10_hit": "top10_hit"}
    mismatch = (n != summary.get("settled_verified_races") or
                any(counts[m] != summary.get(k) for m, k in reported.items()))
    measures = {m: {"hits": counts[m], "n": n,
                    "observed_rate": counts[m] / n if n else None,
                    "wilson_95_interval": wilson(counts[m], n)}
                for m in METRICS}
    return {
        "schema": "BOAT_EDGE_V234_READ_ONLY_CONFIDENCE_AUDIT_V1",
        "scope": "SITE_ONLY_NOT_FORMAL_FRESH",
        "scored_records_read": n,
        "invalid_record_count": len(errors),
        "invalid_records": errors,
        "summary_mismatch": mismatch,
        "metrics": measures,
        "scoring_exclusions_from_latest_run": summary.get("scoring_exclusions_this_run", {}),
        "confidence_interval_not_proof_of_unseen_capture": True,
        "first_git_commit_and_model_sha_independently_reverified": False,
        "paired_candidate_vs_baseline_evaluated": False,
        "calibration_and_log_loss_evaluated": False,
        "accuracy_improvement_proven": False,
        "formal_fresh_scoring_unlocked": False,
        "real_purchases_authorized": False,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("."))
    args = parser.parse_args()
    result = audit(args.root)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2))
    if result["invalid_record_count"] or result["summary_mismatch"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
