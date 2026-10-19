#!/usr/bin/env python3
"""V352: read-only completed-event pressure evidence for C-1.

Consumes V348 --event all metadata; does not inspect jobs, outputs, results,
predictions, freeze bytes, or formal Fresh. No claim of duplicate work or
source-eligible races follows from skipped/cancelled workflow records alone.
"""
from __future__ import annotations
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

SCHEMA = "BOAT_EDGE_01_V352_EVENT_PRESSURE_METADATA_V1"
OWNERS = (
    "BOAT EDGE V216 - Identify Exact Pre-Deadline Source Gaps",
    "BOAT EDGE V229 - Atomic Site Freeze and Pre-result Audit",
    "BOAT EDGE V235 - Stable Autonomous Prediction Freeze and Verified Scoring",
    "BOAT EDGE V220 - Autonomous Site Operations And Guarded Recovery",
    "BOAT EDGE 自動更新",
    "BOAT EDGE 3連単オッズ更新 V71",
)


def analyze(report: dict) -> dict:
    if report.get("schema") != SCHEMA or report.get("event_filter") != "all":
        raise ValueError("V352_REQUIRES_ALL_EVENT_EXPORT")
    rows = report.get("runs")
    if not isinstance(rows, list):
        raise ValueError("V352_RUNS_NOT_ARRAY")
    buckets = defaultdict(list)
    unknown_times = 0
    for r in rows:
        if not isinstance(r, dict):
            raise ValueError("V352_MALFORMED_ROW")
        raw = r.get("created_at")
        try:
            ts = datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
            if ts.tzinfo is None:
                raise ValueError("timezone absent")
        except (ValueError, TypeError):
            unknown_times += 1
            continue
        ts = ts.astimezone(timezone.utc)
        bucket = ts.replace(minute=ts.minute // 5 * 5, second=0, microsecond=0)
        buckets[bucket.isoformat().replace("+00:00", "Z")].append(r)

    windows = []
    for start, rows_here in sorted(buckets.items()):
        conclusions = Counter(str(r.get("conclusion") or "unresolved") for r in rows_here)
        events = Counter(str(r.get("event") or "unknown") for r in rows_here)
        capture = [r for r in rows_here if r.get("workflow_name") in OWNERS]
        capture_status = Counter(str(r.get("conclusion") or "unresolved") for r in capture)
        capture_workflow_run = [r for r in capture if r.get("event") == "workflow_run"]
        windows.append({
            "window_start_utc": start,
            "run_count": len(rows_here),
            "workflow_run_events": events["workflow_run"],
            "scheduled_events": events["schedule"],
            "skipped": conclusions["skipped"],
            "cancelled": conclusions["cancelled"],
            "successful": conclusions["success"],
            "capture_owner_events": len(capture),
            "capture_owner_workflow_run_events": len(capture_workflow_run),
            "capture_owner_skipped": capture_status["skipped"],
            "capture_owner_cancelled": capture_status["cancelled"],
            "capture_owner_names": dict(sorted(Counter(r.get("workflow_name") for r in capture).items())),
            "sample_run_ids": [r["run_id"] for r in rows_here if r.get("run_id") is not None][:20],
        })
    return {
        "schema": "BOAT_EDGE_01_V352_ACTIONS_PRESSURE_REPORT_V1",
        "read_only": True,
        "scope": "PAGINATED_ACTIONS_EVENT_METADATA_NOT_EXECUTED_JOB_PROOF",
        "source_event_filter": report["event_filter"],
        "run_records": len(rows),
        "unknown_or_missing_created_at": unknown_times,
        "windows_observed": len(windows),
        "busiest_five_minute_windows": sorted(
            windows, key=lambda r: (-r["capture_owner_skipped"] - r["capture_owner_cancelled"],
                                    -r["run_count"], r["window_start_utc"]))[:15],
        "all_windows": windows,
        "pagination_may_be_incomplete": True,
        "run_or_job_duplicate_proven": False,
        "capture_source_eligibility_proven": False,
        "workflow_disable_authorized": False,
    }


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: boat_edge_v352_action_pressure.py all-events.json")
    report = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    print(json.dumps(analyze(report), ensure_ascii=False, indent=2, sort_keys=True))
