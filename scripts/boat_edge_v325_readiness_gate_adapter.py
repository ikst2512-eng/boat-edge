#!/usr/bin/env python3
"""V325 classify a V321 readiness row using conservative V324 evidence.

False-by-default for all externally authenticated source/actual-entry gates.
No synthetic booleans may be promoted to verified source evidence.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from boat_edge_v324_research_gate import REQUIREMENTS, evaluate


def classify_site_row(row):
    if not isinstance(row, dict):
        raise ValueError("INVALID_SITE_ROW")
    baseline = row.get("site_baseline_predeadline_metadata") is True
    shadow = row.get("v318_shadow_present") is True
    checks = {key: False for key in REQUIREMENTS}
    checks["baseline_predeadline"] = baseline
    # Presence of a V318 file alone does NOT prove its freeze timing, integrity,
    # race identity or predeadline GitHub server reception.
    checks["candidate_predeadline"] = False
    checks["same_race"] = False
    checks["both_sha256_consistent"] = False
    result = evaluate(checks)
    return {
        "race_key": row.get("race_key"),
        "baseline_predeadline_metadata": baseline,
        "v318_shadow_file_present_unverified": shadow,
        "gate": result,
        "reasons": (
            ["SHADOW_NOT_PRESENT"] if not shadow else ["SHADOW_CONTENT_NOT_AUDITED"]
        ) + (["BASELINE_PREDEADLINE_NOT_VERIFIED"] if not baseline else []),
        "results_read": False,
        "formal_fresh_read": False,
    }


def main():
    parser = argparse.ArgumentParser(description="Conservative V321-to-V324 readiness adapter")
    parser.add_argument("--readiness-report", required=True, type=Path)
    args = parser.parse_args()
    report = json.loads(args.readiness_report.read_text(encoding="utf-8"))
    if report.get("schema") != "BOAT_EDGE_V321_SITE_PROSPECTIVE_READINESS_V1":
        raise ValueError("V321_REPORT_REQUIRED")
    print(json.dumps({
        "schema": "BOAT_EDGE_V325_CONSERVATIVE_GATE_ADAPTER_V1",
        "rows": [classify_site_row(row) for row in report["rows"]],
        "model_promotion_authorized": False,
        "results_read": False,
        "formal_fresh_read": False,
    }, ensure_ascii=False, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
