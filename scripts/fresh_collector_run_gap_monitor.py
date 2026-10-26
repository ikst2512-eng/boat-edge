#!/usr/bin/env python3
"""Read-only collector scheduling gap monitor; never dispatches or writes data."""
import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.request import Request, urlopen

def classify(runs, now, window_minutes=90, max_gap_minutes=20):
    start = now - timedelta(minutes=window_minutes)
    points = sorted(datetime.fromisoformat(r["created_at"].replace("Z", "+00:00"))
                    for r in runs if r.get("created_at"))
    recent = [x for x in points if start <= x <= now]
    scheduled = [r for r in runs if r.get("event") == "schedule" and r.get("created_at")
                 and start <= datetime.fromisoformat(r["created_at"].replace("Z", "+00:00")) <= now]
    # Historical absence cannot prove a missed cron; the host may throttle it.
    intervals = [int((b-a).total_seconds()) for a,b in zip(recent,recent[1:])]
    age = int((now-recent[-1]).total_seconds()) if recent else window_minutes*60
    return {"runs_in_window": len(recent), "scheduled_runs_in_window": len(scheduled),
            "no_scheduled_run_in_window": not scheduled,
            "largest_run_start_gap_seconds": max(intervals, default=None),
            "last_start_age_seconds": age,
            "possible_schedule_gap": age > max_gap_minutes*60 or any(v > max_gap_minutes*60 for v in intervals),
            "meaning": "READ_ONLY_MISSING_RUN_SIGNAL_NOT_SCHEDULER_ROOT_CAUSE"}

def main():
    now = datetime.now(timezone.utc)
    result = {"schema": "BOAT_EDGE_COLLECTOR_RUN_GAP_MONITOR_V1",
              "observed_at_utc": now.isoformat(), "results_accessed": False,
              "formal_unlock_authorized": False, "collector_dispatched": False, "error": None}
    try:
        repo = os.environ["GITHUB_REPOSITORY"]
        token = os.environ["GH_READONLY_TOKEN"]
        runs = []
        complete = False
        oldest_needed = now - timedelta(minutes=90)
        for page in range(1, 11):
            req = Request(f"https://api.github.com/repos/{repo}/actions/workflows/auto-update.yml/runs?per_page=100&page={page}",
                          headers={"Authorization": "Bearer "+token, "Accept": "application/vnd.github+json"})
            with urlopen(req, timeout=20) as resp:
                batch = json.load(resp)["workflow_runs"]
            runs.extend(batch)
            if not batch or min(datetime.fromisoformat(x["created_at"].replace("Z", "+00:00")) for x in batch) < oldest_needed:
                complete = True
                break
        result["pagination_complete_for_window"] = complete
        result["runs_examined"] = len(runs)
        result.update(classify(runs, now))
        if not complete:
            result["possible_schedule_gap"] = None
            result["error"] = "RUN_HISTORY_PAGINATION_INCOMPLETE_NO_GAP_ASSERTION"
    except Exception as exc:
        result["error"] = type(exc).__name__ + ": " + str(exc)
    Path("fresh_collector_run_gap_monitor.json").write_text(json.dumps(result, indent=2)+"\n")
    print(json.dumps(result, sort_keys=True))
    if result["error"]:
        raise SystemExit(2)

if __name__ == "__main__":
    main()
