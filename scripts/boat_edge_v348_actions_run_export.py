#!/usr/bin/env python3
"""V348: optional, read-only GitHub Actions scheduled-run metadata exporter.

Requires GITHUB_TOKEN or GH_TOKEN; never writes to GitHub, and never guesses
changed files from a run's head SHA. Output is stdout JSON only.
"""
from __future__ import annotations
import argparse
import json
import os
import urllib.parse
import urllib.request


def normalize(run: dict) -> dict:
    return {
        "run_id": run["id"],
        "workflow_id": run.get("workflow_id"),
        "workflow_name": run.get("name"),
        "event": run.get("event"),
        "status": run.get("status"),
        "conclusion": run.get("conclusion"),
        "created_at": run.get("created_at"),
        "run_started_at": run.get("run_started_at"),
        "updated_at": run.get("updated_at"),
        "head_sha": run.get("head_sha"),
        "run_url": run.get("html_url"),
        "changed_paths": None,
        "changed_paths_proven": False,
        "completed_at_proven": False,
        "runtime_duplicate_proven": False,
    }


def export_runs(fetch_page, max_pages: int = 3) -> dict:
    if not 1 <= max_pages <= 20:
        raise ValueError("max_pages must be 1..20")
    rows = []
    for page in range(1, max_pages + 1):
        response = fetch_page(page)
        runs = response.get("workflow_runs", [])
        rows.extend(normalize(r) for r in runs if r.get("event") == "schedule")
        if len(runs) < 100:
            break
    return {
        "schema": "BOAT_EDGE_01_V348_SCHEDULED_ACTIONS_RUN_METADATA_V1",
        "read_only": True,
        "run_count": len(rows),
        "runs": rows,
        "changed_file_proof_collected": False,
        "workflow_disable_authorized": False,
        "pagination_may_be_incomplete": True,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True, help="owner/repository")
    parser.add_argument("--max-pages", type=int, default=3)
    args = parser.parse_args()
    if len(args.repo.split("/")) != 2 or any(not s for s in args.repo.split("/")):
        parser.error("--repo must be owner/repository")
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if not token:
        parser.error("GITHUB_TOKEN or GH_TOKEN required (read-only Actions access)")
    def fetch(page):
        query = urllib.parse.urlencode({"event": "schedule", "per_page": 100, "page": page})
        url = f"https://api.github.com/repos/{args.repo}/actions/runs?{query}"
        request = urllib.request.Request(url, headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "User-Agent": "boat-edge-v348-readonly-audit",
        })
        with urllib.request.urlopen(request, timeout=20) as response:
            return json.load(response)
    print(json.dumps(export_runs(fetch, args.max_pages), ensure_ascii=False, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
