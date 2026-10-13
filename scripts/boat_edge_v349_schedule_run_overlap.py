#!/usr/bin/env python3
"""V349: read-only temporal candidate comparison for V348 exported runs.

Updated_at is not a proven completion time. Consequently this script NEVER
claims concurrent execution or duplicate writes from V348 metadata.
"""
from __future__ import annotations
import argparse
import json
from datetime import datetime
from pathlib import Path


def _time(value):
    if not isinstance(value, str) or not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def analyze(export: dict) -> dict:
    if export.get("schema") != "BOAT_EDGE_01_V348_SCHEDULED_ACTIONS_RUN_METADATA_V1":
        raise ValueError("V348_EXPORT_SCHEMA_REQUIRED")
    runs = export.get("runs")
    if not isinstance(runs, list):
        raise ValueError("RUNS_MUST_BE_LIST")
    rows = []
    for run in runs:
        if not isinstance(run, dict) or run.get("event") != "schedule":
            continue
        rows.append({
            "run_id": run.get("run_id"),
            "workflow_name": run.get("workflow_name"),
            "run_started_at": run.get("run_started_at"),
            "updated_at": run.get("updated_at"),
            "start_parseable": _time(run.get("run_started_at")) is not None,
            "completion_time_verified": False,
            "changed_paths_verified": False,
        })
    rows.sort(key=lambda r: (str(r["run_started_at"]), str(r["run_id"])))
    same_start = []
    for i, left in enumerate(rows):
        for right in rows[i + 1:]:
            if (left["start_parseable"] and right["start_parseable"] and
                    left["run_started_at"] == right["run_started_at"] and
                    left["run_id"] != right["run_id"]):
                same_start.append({"left_run_id": left["run_id"], "right_run_id": right["run_id"],
                                   "evidence": "SAME_REPORTED_START_ONLY"})
    return {
        "schema": "BOAT_EDGE_01_V349_SCHEDULED_RUN_TEMPORAL_HINTS_V1",
        "read_only": True,
        "scheduled_run_records": len(rows),
        "same_start_candidate_pairs": same_start,
        "concurrent_runs_proven": 0,
        "duplicate_writes_proven": 0,
        "workflow_disable_authorized": False,
        "limitations": ["updated_at is not completion time",
                        "V348 has no verified changed-file evidence",
                        "same reported start does not prove overlapping execution"],
        "runs": rows,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("export_json", type=Path)
    args = parser.parse_args()
    print(json.dumps(analyze(json.loads(args.export_json.read_text(encoding="utf-8"))),
                     ensure_ascii=False, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
