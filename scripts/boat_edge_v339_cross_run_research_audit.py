#!/usr/bin/env python3
"""V339 SITE-only cross-run research-freeze collision audit.

Accepts explicit V334/V338 JSON run reports downloaded by an operator from
V336 GitHub Actions artifacts. Never fetches outcomes, formal cohorts, odds,
race files, research prediction bodies or network resources. Digests and times
are self-reported by run artifacts, not independently authenticated.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re

MODEL = "BOAT_EDGE_V339_SITE_CROSS_RUN_RESEARCH_COLLISION_AUDIT"
RUNNER = "BOAT_EDGE_V334_SITE_RESEARCH_BATCH_ONLY"
KEY = re.compile(r"^20[0-9]{6}-(?:0[1-9]|1[0-9]|2[0-4])-(?:0[1-9]|1[0-2])$")
SHA = re.compile(r"^[0-9a-f]{64}$")
MODES = {"national_only", "national_motor", "national_motor_st"}


def _check_report(report, index):
    if not isinstance(report, dict) or report.get("model_id") != RUNNER:
        raise ValueError("WRONG_RESEARCH_RUN_REPORT")
    if (report.get("capture_requested") is not True
            or report.get("formal_fresh_read") is not False
            or report.get("results_read") is not False
            or report.get("accuracy_improvement_proven") is not False
            or report.get("production_model_changed") is not False
            or report.get("wagers_authorized") is not False):
        raise ValueError("RESEARCH_ONLY_RUN_FLAGS_REQUIRED")
    window = report.get("window")
    if not isinstance(window, dict):
        raise ValueError("WINDOW_REQUIRED")
    date = window.get("date")
    if (not isinstance(date, str) or not re.fullmatch(r"20[0-9]{6}", date)
            or date == "20261001"):
        raise ValueError("NONFORMAL_DATE_REQUIRED")
    candidates = window.get("candidates")
    completed = report.get("completed")
    failures = report.get("failures")
    if (not isinstance(candidates, list) or not isinstance(completed, list)
            or not isinstance(failures, list)
            or type(report.get("completed_count")) is not int
            or report["completed_count"] != len(completed)):
        raise ValueError("REPORT_COUNTS_OR_LISTS_INVALID")
    selected = []
    for row in candidates:
        key = row.get("race_key") if isinstance(row, dict) else None
        if not isinstance(key, str) or KEY.fullmatch(key) is None or key[:8] != date:
            raise ValueError("INVALID_SELECTED_RACE")
        selected.append(key)
    if len(selected) != len(set(selected)) or len(selected) > 12:
        raise ValueError("DUPLICATE_OR_OVERSIZED_SELECTION")
    if isinstance(window.get("coverage"), dict):
        coverage = window["coverage"]
        if coverage.get("selected") != len(selected):
            raise ValueError("INCONSISTENT_COVERAGE_COUNT")
    seen = set()
    accepted = []
    for row in completed:
        if not isinstance(row, dict):
            raise ValueError("INVALID_COMPLETED_ROW")
        key, digest, path = row.get("race_key"), row.get("sha256"), row.get("path")
        if not isinstance(key, str) or key not in selected or key in seen:
            raise ValueError("UNSELECTED_OR_DUPLICATE_FROZEN_RACE")
        if not isinstance(digest, str) or SHA.fullmatch(digest) is None:
            raise ValueError("INVALID_RESEARCH_FREEZE_DIGEST")
        expected_path = f"data/research_local_v332/{date}/{key}.json"
        if path != expected_path:
            raise ValueError("UNEXPECTED_RESEARCH_FREEZE_PATH")
        if not isinstance(row.get("modes"), list) or set(row["modes"]) != MODES or len(row["modes"]) != 3:
            raise ValueError("PREDECLARED_ABLATION_MODES_REQUIRED")
        seen.add(key)
        accepted.append((key, digest, index))
    failed = set()
    for row in failures:
        key = row.get("race_key") if isinstance(row, dict) else None
        if (not isinstance(key, str) or key not in selected
                or key in seen or key in failed or not isinstance(row.get("reason"), str)):
            raise ValueError("INVALID_OR_DUPLICATE_FAILURE")
        failed.add(key)
    return {"date": date, "selected": len(selected),
            "completed": len(completed), "failed": len(failures),
            "accepted": accepted}


def audit(reports):
    if not isinstance(reports, list) or not reports:
        raise ValueError("EXPLICIT_REPORT_LIST_REQUIRED")
    validated = [_check_report(report, i + 1) for i, report in enumerate(reports)]
    by_race = {}
    for report in validated:
        for key, digest, index in report["accepted"]:
            by_race.setdefault(key, []).append({"report_index": index, "sha256": digest})
    repeats = {}
    divergent = {}
    for key, occurrences in sorted(by_race.items()):
        if len(occurrences) > 1:
            repeats[key] = occurrences
            if len({x["sha256"] for x in occurrences}) > 1:
                divergent[key] = occurrences
    return {
        "model_id": MODEL,
        "explicit_report_count": len(validated),
        "total_selected_across_reports": sum(x["selected"] for x in validated),
        "total_local_freezes_across_reports": sum(x["completed"] for x in validated),
        "total_failed_attempts_across_reports": sum(x["failed"] for x in validated),
        "distinct_frozen_race_keys_within_supplied_reports": len(by_race),
        "cross_run_repeat_race_count": len(repeats),
        "cross_run_divergent_sha_race_count": len(divergent),
        "repeated_races": repeats,
        "divergent_races": divergent,
        "unique_within_supplied_reports_only": not repeats,
        "complete_actions_history_or_global_uniqueness_attested": False,
        "freeze_bytes_independently_rehashed": False,
        "timestamps_independently_authenticated": False,
        "eligible_for_formal_fresh_scoring": False,
        "accuracy_improvement_proven": False,
        "formal_fresh_read": False,
        "results_read": False,
        "writes_performed": False,
    }


def main():
    parser = argparse.ArgumentParser(description="Read-only audit of explicitly supplied V336 Action reports")
    parser.add_argument("--reports", required=True, type=Path, nargs="+")
    args = parser.parse_args()
    reports = [json.loads(path.read_text(encoding="utf-8")) for path in args.reports]
    print(json.dumps(audit(reports), sort_keys=True, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
