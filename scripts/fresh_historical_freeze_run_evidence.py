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

# These are the minutes in each existing workflow's UTC cron definition.
# A cron opportunity is not evidence that GitHub Actions actually dispatched.
CRON_MINUTES = {"v229": tuple(range(1, 60, 5)), "v216": tuple(range(4, 60, 5))}

def configured_schedule_slots(start, end, workflow_name):
    first = start.astimezone(timezone.utc).replace(second=0, microsecond=0)
    last = end.astimezone(timezone.utc)
    slots = []
    while first <= last:
        if first.minute in CRON_MINUTES[workflow_name]:
            if workflow_name != "v229" or first.hour in (*range(0, 15), 23):
                slots.append(first.astimezone(JST).isoformat())
        first += timedelta(minutes=1)
    return slots

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
        found, overlaps, uncertain, nearby, covered = [], [], [], [], False
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
                if start_utc - timedelta(minutes=20) <= stamp <= end_utc + timedelta(minutes=20):
                    nearby.append(evidence)
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
        nearby.sort(key=lambda x: (x["run_started_at"], x["id"]))
        # Inspect actual job boundaries for nearby runs. Workflow updated_at
        # alone cannot prove a job was running during the freeze window.
        job_evidence = []
        for candidate in nearby[:30]:
            run_id = candidate.get("id")
            if type(run_id) is not int:
                raise ValueError("INVALID_RUN_ID")
            url = f"https://api.github.com/repos/{repo}/actions/runs/{run_id}/jobs?per_page=100&page=1"
            response = get_json(url, token)
            jobs = response.get("jobs")
            total = response.get("total_count")
            if not isinstance(jobs, list) or type(total) is not int or total != len(jobs):
                # Ambiguous pagination: reject completeness, never count as absent.
                result["evidence_complete"] = False
                job_evidence.append({"run_id": run_id, "complete": False, "jobs": []})
                continue
            detailed = []
            for job in jobs:
                started = job.get("started_at")
                ended = job.get("completed_at")
                if not started or not ended:
                    detailed.append({"id": job.get("id"), "timing_complete": False,
                                     "overlaps_window": None})
                    result["evidence_complete"] = False
                    continue
                js = datetime.fromisoformat(started.replace("Z", "+00:00"))
                je = datetime.fromisoformat(ended.replace("Z", "+00:00"))
                if je < js:
                    raise ValueError("INVALID_JOB_TIMING")
                detailed.append({"id": job.get("id"), "name": job.get("name"),
                                 "conclusion": job.get("conclusion"), "started_at": started,
                                 "completed_at": ended, "timing_complete": True,
                                 "overlaps_window": js <= end_utc and je >= start_utc})
            job_evidence.append({"run_id": run_id, "complete": True, "jobs": detailed})
        if len(nearby) > 30:
            result["evidence_complete"] = False
        result["workflows"][name] = {
            "workflow": workflow,
            "configured_cron_slots_jst_not_dispatch_proof": configured_schedule_slots(start, end, name),
            "runs_started_in_window": found,
            "possible_overlaps_by_updated_at": overlaps,
            "nearby_starts_plus_minus_20m": nearby,
            "nearby_job_timing": job_evidence,
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
