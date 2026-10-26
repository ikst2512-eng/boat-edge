#!/usr/bin/env python3
"""Read-only GitHub Actions run chronology for the collector; no race results."""
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

START = datetime.fromisoformat("2026-10-26T05:15:00+00:00")
END = datetime.fromisoformat("2026-10-26T06:20:00+00:00")
repo = os.getenv("GITHUB_REPOSITORY", "")
token = os.getenv("GH_READONLY_TOKEN", "")
report = {"schema": "BOAT_EDGE_COLLECTOR_ACTIONS_TIMELINE_V1",
          "window_start_utc": START.isoformat(), "window_end_utc": END.isoformat(),
          "results_accessed": False, "formal_unlock_authorized": False,
          "runs": [], "upstream_v71_runs": [], "error": None}
try:
    if not repo or not token:
        raise RuntimeError("MISSING_GITHUB_READ_ACCESS")
    url = f"https://api.github.com/repos/{repo}/actions/workflows/auto-update.yml/runs?per_page=100"
    for page in range(1, 6):
        req = Request(url + f"&page={page}", headers={
            "Authorization": "Bearer " + token,
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28"})
        with urlopen(req, timeout=20) as resp:
            data = json.load(resp)
        runs = data.get("workflow_runs", [])
        for r in runs:
            created = datetime.fromisoformat(r["created_at"].replace("Z", "+00:00"))
            if START <= created <= END:
                report["runs"].append({k: r.get(k) for k in (
                    "id", "event", "status", "conclusion", "created_at", "run_started_at",
                    "updated_at", "head_sha", "head_branch", "html_url", "run_attempt")})
        if not runs or min(datetime.fromisoformat(r["created_at"].replace("Z", "+00:00")) for r in runs) < START:
            break
    # Compare independent V71 source producer starts within the same fixed window.
    # This does not infer causality from timing alone.
    producer_url = f"https://api.github.com/repos/{repo}/actions/runs?per_page=100"
    for page in range(1, 6):
        req = Request(producer_url + f"&page={page}", headers={
            "Authorization": "Bearer " + token,
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28"})
        with urlopen(req, timeout=20) as resp:
            data = json.load(resp)
        runs = data.get("workflow_runs", [])
        for r in runs:
            created = datetime.fromisoformat(r["created_at"].replace("Z", "+00:00"))
            if START <= created <= END and r.get("name") == "BOAT EDGE 3連単オッズ更新 V71":
                report["upstream_v71_runs"].append({k: r.get(k) for k in (
                    "id", "event", "status", "conclusion", "created_at", "run_started_at",
                    "updated_at", "head_sha", "html_url")})
        if not runs or min(datetime.fromisoformat(r["created_at"].replace("Z", "+00:00")) for r in runs) < START:
            break
    report["upstream_v71_runs"].sort(key=lambda r: r["created_at"])
    report["matched_upstream_v71_runs"] = len(report["upstream_v71_runs"])
    # API workflow metadata distinguishes disabled workflows from missing schedule events.
    report["workflow_status"] = {}
    for filename in ("auto-update.yml",):
        req = Request(f"https://api.github.com/repos/{repo}/actions/workflows/{filename}", headers={
            "Authorization": "Bearer " + token,
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28"})
        with urlopen(req, timeout=20) as resp:
            metadata = json.load(resp)
        report["workflow_status"][filename] = {k: metadata.get(k) for k in (
            "id", "name", "state", "path", "created_at", "updated_at")}
    report["runs"].sort(key=lambda r: r["created_at"])
    report["matched_runs"] = len(report["runs"])
except Exception as exc:
    report["error"] = type(exc).__name__ + ": " + str(exc)
Path("fresh_collector_actions_timeline.json").write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps(report, sort_keys=True))
if report["error"]:
    raise SystemExit(2)
