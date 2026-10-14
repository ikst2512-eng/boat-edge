"""Read-only Pages verification and narrowly gated rebuild request.

V251 never edits site predictions, race data or formal Fresh. A manual Pages
build is requested only when the repository is configured for legacy branch
deployment, main has been quiet, and no current build is already processing.
"""
from __future__ import annotations
from datetime import datetime, timezone
import json
import os
import sys
import urllib.error
import urllib.request

PAGE_PATH = "dynamic/pages/pages-build-deployment"
WAIT_SECONDS = 180
# A successful Pages deploy for an OLDER head is not proof the current
# SITE PRE_RESULT prediction is available. Give GitHub a short settling
# window, then permit a narrowly gated recovery of the still-unpublished head.
PUBLISH_GRACE_SECONDS = 240


def parse_time(s: str | None):
    if not s:
        return None
    try:
        d = datetime.fromisoformat(str(s).replace("Z", "+00:00"))
        return d if d.tzinfo else None
    except (ValueError, TypeError):
        return None


def decision(pages, commit, runs, now=None):
    """Return an auditable decision string, without calling GitHub.

    In particular, CANCELLED does not mean an outage if a more recent
    SUCCESS exists. Never request deployment if the source is not main.
    """
    now = now or datetime.now(timezone.utc)
    if not isinstance(pages, dict) or not isinstance(commit, dict):
        return "NO_VERIFIABLE_CONFIGURATION"
    if pages.get("build_type") != "legacy":
        return "NOT_BRANCH_BASED_PAGES"
    if (pages.get("source") or {}).get("branch") != "main":
        return "PAGES_SOURCE_NOT_MAIN"
    head = str(commit.get("sha") or "")
    if len(head) != 40 or not all(c in "0123456789abcdef" for c in head.lower()):
        return "INVALID_HEAD"
    commit_time = parse_time(((commit.get("commit") or {}).get("committer") or {}).get("date"))
    if commit_time is None:
        return "HEAD_TIME_UNVERIFIED"
    lag = (now - commit_time).total_seconds()
    if lag < WAIT_SECONDS:
        return "HEAD_STILL_CHANGING"
    if lag < 0:
        return "HEAD_TIME_IN_FUTURE"
    builds = [r for r in runs if isinstance(r, dict) and r.get("path") == PAGE_PATH]
    if not builds:
        return "NO_PAGES_RUN_EVIDENCE"
    latest = builds[0]
    last_ok = next((r for r in builds if r.get("conclusion") == "success"), None)
    if last_ok and last_ok.get("head_sha") == head:
        return "CURRENT_COMMIT_PUBLISHED"
    if any(r.get("status") in ("queued", "in_progress", "waiting", "pending", "requested")
           for r in builds[:4]):
        return "PAGES_BUILD_ALREADY_ACTIVE"
    if last_ok:
        latest_success = parse_time(last_ok.get("updated_at") or last_ok.get("created_at"))
        if latest_success and (now - latest_success).total_seconds() < PUBLISH_GRACE_SECONDS:
            # This success was for a *different* head (exact match already
            # returned above). Do not suppress current PRE_RESULT publication
            # for the former twelve-minute grace interval.
            return "RECENT_PAGES_SUCCESS_GRACE"
    last_build = parse_time(latest.get("created_at"))
    if last_build and (now - last_build).total_seconds() < WAIT_SECONDS:
        return "RECENT_PAGE_BUILD_WAIT"
    return "REQUEST_LEGACY_PAGES_BUILD"


def api_json(root, path, token):
    headers = {"Accept": "application/vnd.github+json",
               "X-GitHub-Api-Version": "2022-11-28",
               "Authorization": "Bearer " + token,
               "User-Agent": "BOAT-EDGE-pages-recovery-v251"}
    request = urllib.request.Request(root + path, headers=headers)
    with urllib.request.urlopen(request, timeout=20) as response:
        return json.load(response)


def main():
    repo = os.environ.get("GITHUB_REPOSITORY", "")
    token = os.environ.get("GITHUB_TOKEN", "")
    if not repo or not token or "/" not in repo:
        print("V251_GITHUB_AUTH_UNAVAILABLE_NO_ACTION")
        return 0
    root = "https://api.github.com/repos/" + repo
    try:
        pages = api_json(root, "/pages", token)
        commit = api_json(root, "/commits/main", token)
        runs = api_json(root, "/actions/runs?per_page=100", token).get("workflow_runs", [])
        outcome = decision(pages, commit, runs)
        print("V251_DECISION", outcome)
        print("V251_MAIN", str(commit.get("sha", ""))[:12])
        if outcome != "REQUEST_LEGACY_PAGES_BUILD":
            return 0
        request = urllib.request.Request(root + "/pages/builds", data=b"{}",
            method="POST", headers={"Authorization": "Bearer " + token,
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
                "Content-Type": "application/json",
                "User-Agent": "BOAT-EDGE-pages-recovery-v251"})
        with urllib.request.urlopen(request, timeout=25) as response:
            print("V251_BUILD_REQUEST_HTTP", response.status,
                  "(request accepted; publication NOT yet confirmed)")
        return 0
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError,
            KeyError, ValueError) as exc:
        print("V251_REBUILD_NOT_CONFIRMED", type(exc).__name__,
              str(exc)[:160], "(fail closed; no site or model mutations)")
        return 0


if __name__ == "__main__":
    sys.exit(main())
