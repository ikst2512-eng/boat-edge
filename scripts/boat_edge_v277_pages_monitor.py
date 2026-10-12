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
    # V287: Pages must publish the actual scripts used by the mobile
    # Autopilot view, not only the parent HTML. Missing/stale JS fails closed.
    "assets/boat_edge_v278_next_watch.js",
    "assets/boat_edge_v286_freeze_evidence.js",
    "assets/boat_edge_v252_prospective.js",
    "assets/boat_edge_v253_misses.js",
    "assets/boat_edge_v254_tail_status.js",
    "assets/boat_edge_v255_confidence.js",
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


def same_ui_lineage(latest_ui_commits, deployed_ui_commits):
    """Every tracked UI path must have the same latest modifying commit in both trees.

    Commit timestamps alone cannot prove the deployed build includes the current
    UI; this checks the content lineage of the deployment's actual head SHA.
    """
    if not isinstance(latest_ui_commits, list) or not isinstance(deployed_ui_commits, list):
        return False
    if not latest_ui_commits or len(latest_ui_commits) != len(deployed_ui_commits):
        return False
    for current, deployed in zip(latest_ui_commits, deployed_ui_commits):
        if not isinstance(current, dict) or not isinstance(deployed, dict):
            return False
        c, d = current.get("sha"), deployed.get("sha")
        if (not isinstance(c, str) or not isinstance(d, str) or
                len(c) != 40 or len(d) != 40 or
                any(x not in "0123456789abcdef" for x in c.lower()) or
                any(x not in "0123456789abcdef" for x in d.lower()) or
                c.lower() != d.lower()):
            return False
    return True


def report(runs, latest_ui_commits, now=None, deployed_ui_commits=None):
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
    lineage_verified = bool(last_ok) and same_ui_lineage(latest_ui_commits, deployed_ui_commits)
    if lineage_verified:
        status = "LATEST_UI_COVERED_BY_SUCCESSFUL_ACTIONS"
    elif active:
        status = "UI_PUBLISH_PENDING_ACTIVE_BUILD"
    elif now < newest_ui:
        status = "CLOCK_SKEW_UNVERIFIED"
    elif (now - newest_ui).total_seconds() <= MAX_LAG_SECONDS:
        status = "UI_RECENTLY_CHANGED_WAIT_FOR_PUBLISH"
    elif last_ok and deployed_ui_commits is None:
        status = "PAGES_UI_LINEAGE_UNVERIFIED"
    else:
        status = "UI_PUBLISH_OVERDUE_NEEDS_ATTENTION"
    return {
        "status": status,
        "ui_lineage_verified": lineage_verified,
        "ui_lineage_paths_checked": len(latest_ui_commits) if deployed_ui_commits is not None else 0,
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
        # Resolve each tracked UI path again at the actual successful Pages
        # deployment SHA. Identical last-touch commits prove deployed tree
        # includes the latest UI paths despite unrelated high-frequency data pushes.
        successful = next((run for run in sorted(
            (x for x in runs if x.get("name") == "pages build and deployment"
             or x.get("path") == "dynamic/pages/pages-build-deployment"),
            key=lambda x: parse_date(x.get("created_at"))
            or datetime.min.replace(tzinfo=timezone.utc), reverse=True)
            if run.get("conclusion") == "success" and run.get("status") == "completed"), None)
        deployed = None
        if successful:
            from urllib.parse import quote
            head = successful.get("head_sha")
            if (not isinstance(head, str) or len(head) != 40 or
                    any(ch not in "0123456789abcdef" for ch in head.lower())):
                raise ValueError("V285_PAGES_DEPLOYED_HEAD_UNVERIFIED")
            deployed = []
            for path in UI_PATHS:
                suffix = "/commits?sha=" + head + "&path=" + quote(path, safe="") + "&per_page=1"
                rows = api(repo, suffix, token)
                if not isinstance(rows, list) or len(rows) != 1:
                    raise ValueError("V285_DEPLOYED_UI_LINEAGE_UNVERIFIED")
                deployed.append(rows[0])
        data = report(runs, commits, deployed_ui_commits=deployed)
        data["schema"] = "BOAT_EDGE_V285_PAGES_UI_LINEAGE_PROOF_V1"
        data["run_purpose"] = "MONITOR_ONLY_NO_REDEPLOY_NO_GIT_WRITE_NO_RESULT_ACCESS"
        print(json.dumps(data, indent=2, ensure_ascii=False, sort_keys=True))
        with open(os.environ.get("GITHUB_STEP_SUMMARY", "/dev/null"), "a", encoding="utf-8") as out:
            out.write("## BOAT EDGE GitHub Pages evidence (no Safari claim)\n")
            out.write("- Status: " + data["status"] + "\n")
            out.write("- Latest UI commit: " + str(data.get("newest_ui_commit_sha")) + "\n")
            out.write("- Last deployed run: " + str(data.get("last_pages_success_sha")) + "\n")
            out.write("- Tracked UI lineage SHA match: " + str(data.get("ui_lineage_verified")) + "\n")
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
