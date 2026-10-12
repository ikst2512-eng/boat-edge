#!/usr/bin/env python3
"""GitHub Pages publication audit that never treats replaced deployments as outages.

Reads ONLY GitHub Actions, main commit history of UI file paths, and public
repository metadata. It neither reads race/results/formal files nor modifies
GitHub settings, predictions, or pages. A SUCCESS proves an Actions deployment,
not a Safari visual inspection.
"""
from __future__ import annotations

from datetime import datetime, timezone
import json
import os
import sys
import urllib.error
import urllib.request

UI_PATHS = (
    "index.html",
    "autopilot.html",
    "results.html",
    "assets/boat_edge_v177_latest_bridge.js",
    "assets/boat_edge_v204_prediction.js",
    "assets/boat_edge_v241_results.js",
)
MAX_LAG_SECONDS = 900


def parse_date(value):
    if not isinstance(value, str):
        return None
    try:
        stamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return stamp.astimezone(timezone.utc) if stamp.tzinfo else None
    except ValueError:
        return None


def report(runs, latest_ui_commits, now=None):
    now = now or datetime.now(timezone.utc)
    pages = sorted(
        (r for r in runs if isinstance(r, dict) and
         (r.get("name") == "pages build and deployment" or
          r.get("path") == "dynamic/pages/pages-build-deployment")),
        key=lambda r: parse_date(r.get("created_at")) or datetime.min.replace(tzinfo=timezone.utc),
        reverse=True,
    )
    successes = [r for r in pages if r.get("conclusion") == "success" and r.get("status") == "completed"]
    cancelled = [r for r in pages if r.get("conclusion") == "cancelled"]
    active = [r for r in pages if r.get("status") in ("queued", "in_progress", "pending", "waiting")]
    last_ok = successes[0] if successes else None
    last_ok_start = parse_date((last_ok or {}).get("created_at"))
    last_ok_end = parse_date((last_ok or {}).get("updated_at"))
    ui_times = []
    for row in latest_ui_commits:
        if not isinstance(row, dict) or not isinstance(row.get("sha"), str):
            return {"status": "UI_COMMIT_SOURCE_UNVERIFIED", "cancelled_recent": None}
        d = parse_date(((row.get("commit") or {}).get("committer") or {}).get("date"))
        if d is None:
            return {"status": "UI_COMMIT_SOURCE_UNVERIFIED", "cancelled_recent": None}
        ui_times.append((d, row["sha"]))
    if not ui_times:
        return {"status": "UI_COMMIT_SOURCE_UNVERIFIED", "cancelled_recent": None}
    newest_ui, newest_sha = max(ui_times)
    recent = [r for r in pages if (t:=parse_date(r.get("created_at"))) is not None
              and 0 <= (now - t).total_seconds() <= 3600]
    recent_cancelled = sum(r.get("conclusion") == "cancelled" for r in recent)
    if last_ok_start is not None and last_ok_start >= newest_ui:
        status = "LATEST_UI_COVERED_BY_SUCCESSFUL_ACTIONS"
    elif active:
        status = "UI_PUBLISH_PENDING_ACTIVE_BUILD"
    elif now < newest_ui:
        status = "CLOCK_SKEW_UNVERIFIED"
    elif (now - newest_ui).total_seconds() <= MAX_LAG_SECONDS:
        status = "UI_RECENTLY_CHANGED_WAIT_FOR_PUBLISH"
    else:
        status = "UI_PUBLISH_OVERDUE_NEEDS_ATTENTION"
    return {
        "status": status,
        "last_pages_success_sha": (last_ok or {}).get("head_sha"),
        "last_pages_success_started_utc": last_ok_start.isoformat() if last_ok_start else None,
        "last_pages_success_finished_utc": last_ok_end.isoformat() if last_ok_end else None,
        "newest_ui_commit_sha": newest_sha,
        "newest_ui_commit_utc": newest_ui.isoformat(),
        "pages_success_recent": sum(r.get("conclusion") == "success" for r in recent),
        "pages_cancelled_recent": recent_cancelled,
        "pages_runs_last_hour": len(recent),
        "pages_build_active": bool(active),
        "ui_checked_in_safari": False,
        "accuracy_improvement_proven": False,
    }


def api(repo, suffix, token):
    url = "https://api.github.com/repos/" + repo + suffix
    req = urllib.request.Request(url, headers={
        "Authorization": "Bearer " + token,
        "Accept": "application/vnd.github+json",
        "User-Agent": "BOAT-EDGE-V277-Pages-Monitor",
        "X-GitHub-Api-Version": "2022-11-28",
    })
    with urllib.request.urlopen(req, timeout=15) as stream:
        return json.load(stream)


def main():
    repo, token = os.environ.get("GITHUB_REPOSITORY"), os.environ.get("GITHUB_TOKEN")
    if not repo or not token or repo.count("/") != 1:
        print("V277_PAGE_AUDIT_NO_API_CREDENTIAL_NO_VERIFIED_CLAIM")
        return 2
    try:
        runs = api(repo, "/actions/runs?per_page=100", token)["workflow_runs"]
        commits = []
        for path in UI_PATHS:
            from urllib.parse import quote
            rows = api(repo, "/commits?sha=main&path=" + quote(path, safe="") + "&per_page=1", token)
            if not isinstance(rows, list) or not rows:
                print("V277_UI_PATH_UNVERIFIED", path)
                return 2
            commits.append(rows[0])
        data = report(runs, commits)
        data["schema"] = "BOAT_EDGE_V277_PAGES_READ_ONLY_V1"
        data["run_purpose"] = "MONITOR_ONLY_NO_REDEPLOY_NO_GIT_WRITE_NO_RESULT_ACCESS"
        print(json.dumps(data, indent=2, ensure_ascii=False, sort_keys=True))
        with open(os.environ.get("GITHUB_STEP_SUMMARY", "/dev/null"), "a", encoding="utf-8") as out:
            out.write("## BOAT EDGE GitHub Pages evidence (no Safari claim)\n")
            out.write("- Status: " + data["status"] + "\n")
            out.write("- Latest UI commit: " + str(data.get("newest_ui_commit_sha")) + "\n")
            out.write("- Last deployed run: " + str(data.get("last_pages_success_sha")) + "\n")
            out.write("- Cancelled runs last hour: " + str(data.get("pages_cancelled_recent")) + "\n")
        return 0 if data["status"] in (
            "LATEST_UI_COVERED_BY_SUCCESSFUL_ACTIONS",
            "UI_PUBLISH_PENDING_ACTIVE_BUILD",
            "UI_RECENTLY_CHANGED_WAIT_FOR_PUBLISH") else 1
    except (OSError, urllib.error.URLError, ValueError, KeyError, TypeError) as e:
        print("V277_UNVERIFIED_FAIL_CLOSED", type(e).__name__)
        return 2


if __name__ == "__main__":
    sys.exit(main())
