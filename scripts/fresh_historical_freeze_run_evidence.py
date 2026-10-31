#!/usr/bin/env python3
"""Read-only GitHub Actions evidence for an actual historical freeze window.

No result, odds, prediction, or Formal Fresh data are loaded. A missing run in
the returned API page is NOT proof of a scheduler failure.
"""
from __future__ import annotations
import argparse
import json
import os
from datetime import datetime, timedelta, timezone
from urllib.parse import quote
from urllib.request import Request, urlopen

JST = timezone(timedelta(hours=9))
WORKFLOWS = {
    "v229": "BOAT_EDGE_V229_ATOMIC_FREEZE_AUDIT.yml",
    "v216": "BOAT_EDGE_V216_SOURCE_DIAGNOSTIC.yml",
}
RACES = {
    "20261031-23-06": ("2026-10-31", "11:01"),
    "20261031-24-09": ("2026-10-31", "19:14"),
}

def window(date: str, hhmm: str):
    deadline = datetime.fromisoformat(date + "T" + hhmm + ":00").replace(tzinfo=JST)
    return deadline - timedelta(minutes=10), deadline - timedelta(minutes=2)

def collect(repo, token, race_key, get_json, pages=10):
    if race_key not in RACES:
        raise ValueError("UNAPPROVED_RACE_KEY")
    if not repo or not token:
        raise ValueError("MISSING_GITHUB_READ_ACCESS")
    if pages < 1 or pages > 20:
        raise ValueError("INVALID_PAGE_LIMIT")
    start, end = window(*RACES[race_key])
    start_utc, end_utc = start.astimezone(timezone.utc), end.astimezone(timezone.utc)
    result = {"schema": "BOAT_EDGE_HISTORICAL_FREEZE_RUN_EVIDENCE_V1",
              "race_key": race_key, "window_start_jst": start.isoformat(),
              "window_end_jst": end.isoformat(),
              "results_accessed": False, "formal_unlock_authorized": False,
              "workflows": {}, "evidence_complete": True}
    for name, workflow in WORKFLOWS.items():
        found, overlaps, uncertain, covered = [], [], [], False
        # Query by created date, then inspect actual start separately. Late
        # starts may arise from earlier queued runs, which this scan includes
        # only if created on this day or the prior day.
        begin = (start_utc - timedelta(days=1)).date().isoformat()
        finish = end_utc.date().isoformat()
        for page in range(1, pages + 1):
            url = (f"https://api.github.com/repos/{repo}/actions/workflows/"
                   f"{quote(workflow)}/runs?per_page=100&page={page}"
                   f"&created={begin}..{finish}")
            data = get_json(url, token)
            runs = data.get("workflow_runs")
            if not isinstance(runs, list):
                raise ValueError("INVALID_ACTIONS_RESPONSE")
            for run in runs:
                started = run.get("run_started_at")
                if not started:
                    continue
                stamp = datetime.fromisoformat(started.replace("Z", "+00:00"))
                evidence = {k: run.get(k) for k in (
                    "id", "status", "conclusion", "event", "created_at",
                    "run_started_at", "updated_at", "html_url", "head_sha")}
                if start_utc <= stamp <= end_utc:
                    found.append(evidence)
                if stamp <= end_utc:
                    finished = run.get("updated_at")
                    if not finished:
                        uncertain.append(evidence)
                    else:
                        finish_stamp = datetime.fromisoformat(finished.replace("Z", "+00:00"))
                        if finish_stamp >= start_utc:
                            # updated_at is not a verified job completion time.
                            overlaps.append(evidence)
            if len(runs) < 100:
                covered = True
                break
        found.sort(key=lambda x: (x["run_started_at"], x["id"]))
        overlaps.sort(key=lambda x: (x["run_started_at"], x["id"]))
        result["workflows"][name] = {
            "workflow": workflow, "runs_started_in_window": found,
            "possible_overlaps_by_updated_at": overlaps,
            "uncertain_without_updated_at": uncertain,
            "overlap_is_confirmed_by_job_times": False,
            "pagination_exhausted": covered,
            "no_run_proven": False,  # cannot prove scheduling from this alone
        }
        if not covered:
            result["evidence_complete"] = False
    return result

def github_json(url, token):
    request = Request(url, headers={
        "Authorization": "Bearer " + token,
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28"})
    with urlopen(request, timeout=20) as response:
        return json.load(response)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--race-key", action="append", choices=sorted(RACES), required=True)
    parser.add_argument("--output", default="historical_freeze_run_evidence.json")
    args = parser.parse_args()
    reports = [collect(os.getenv("GITHUB_REPOSITORY", ""),
                       os.getenv("GH_READONLY_TOKEN", ""), key, github_json)
               for key in dict.fromkeys(args.race_key)]
    with open(args.output, "w", encoding="utf-8") as out:
        json.dump({"reports": reports}, out, indent=2, ensure_ascii=False)
        out.write("\n")
    print(json.dumps({"reports": reports}, ensure_ascii=False))

if __name__ == "__main__":
    main()
