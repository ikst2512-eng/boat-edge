#!/usr/bin/env python3
"""V321 prospective SITE-only evidence readiness audit (never score outcomes).

Discovers only known pre-result directories and safe JSON filenames. It never
opens formal Fresh, results, odds, payout or combined race endpoints.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import re

from boat_edge_v320_site_v232_baseline_adapter import baseline_from_v232
from boat_edge_v318_shadow_freeze import KEY

BASELINE_DIR = Path("data/site_autopilot/v232_cohort")
SHADOW_DIR = Path("data/research_shadow_v318")


def audit(root, date):
    if not isinstance(date, str) or re.fullmatch(r"20[0-9]{6}", date) is None:
        raise ValueError("DATE_YYYYMMDD_REQUIRED")
    root = root.resolve()
    base = root / BASELINE_DIR
    paths = sorted(base.glob(date + "-??-??.json")) if base.is_dir() else []
    rows = []
    for path in paths:
        if path.is_symlink() or KEY.fullmatch(path.stem) is None:
            continue
        row = {"race_key": path.stem}
        try:
            baseline = baseline_from_v232(json.loads(path.read_text(encoding="utf-8")))
            if baseline["race_key"] != path.stem:
                raise ValueError("FILENAME_RACE_KEY_MISMATCH")
            row["site_baseline_predeadline_metadata"] = True
            row["site_model_id"] = baseline["model_id"]
            row["baseline_reasons"] = []
        except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError) as exc:
            row["site_baseline_predeadline_metadata"] = False
            row["site_model_id"] = None
            row["baseline_reasons"] = [str(exc)[:100]]
        shadow = root / SHADOW_DIR / date / (path.stem + ".json")
        row["v318_shadow_present"] = shadow.is_file() and not shadow.is_symlink()
        row["three_provider_capture_proven"] = False
        row["independent_actual_entry_proven"] = False
        row["independent_source_authentication_proven"] = False
        row["paired_prediction_accuracy_evaluated"] = False
        row["research_ready_for_accuracy_scoring"] = False
        rows.append(row)
    return {
        "schema": "BOAT_EDGE_V321_SITE_PROSPECTIVE_READINESS_V1",
        "date": date,
        "baseline_file_count": len(rows),
        "baseline_predeadline_metadata_count": sum(r["site_baseline_predeadline_metadata"] for r in rows),
        "v318_shadow_file_count": sum(r["v318_shadow_present"] for r in rows),
        "three_source_independently_proven_count": 0,
        "verified_actual_entry_count": 0,
        "ready_for_accuracy_scoring_count": 0,
        "rows": rows,
        "only_site_pre_result_files_read": True,
        "formal_fresh_read": False,
        "results_read": False,
        "performance_improvement_proven": False,
    }


def main():
    parser = argparse.ArgumentParser(description="SITE-only pre-result readiness audit")
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--date", required=True)
    args = parser.parse_args()
    print(json.dumps(audit(args.root, args.date), sort_keys=True, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
