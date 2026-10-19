#!/usr/bin/env python3
"""Gate 1C: inspect Actions starts in already-missed PRE_RESULT save windows.

Read-only metadata comparison; absence of a run start does NOT establish
source eligibility, confirm that no earlier job was active, or prove a
scheduler outage. Never accesses results, payouts, or formal predictions.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import re
import urllib.parse
import urllib.request

JST = timezone(timedelta(hours=9))
KEY = re.compile(r"^20\d{6}-\d{2}-\d{2}$")
OWNERS = {
    "BOAT EDGE V229 - Atomic Site Freeze and Pre-result Audit": "v229",
    "BOAT EDGE V216 - Identify Exact Pre-Deadline Source Gaps": "v216",
    "BOAT EDGE V125 Revision Safe FINAL15M Audit": "v125_schedule",
    "BOAT EDGE V220 - Autonomous Site Operations And Guarded Recovery": "v220",
    "BOAT EDGE V235 - Stable Autonomous Prediction Freeze and Verified Scoring": "v235",
    "BOAT EDGE 自動更新": "collector",
    "BOAT EDGE 3連単オッズ更新 V71": "odds",
}


def utc_string(value):
    return value.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def deadline_for(key, clock):
    if not KEY.fullmatch(str(key)) or not re.fullmatch(r"\d{2}:\d{2}", str(clock)):
        return None
    try:
        return datetime.strptime(key[:8] + clock, "%Y%m%d%H:%M").replace(tzinfo=JST)
    except ValueError:
        return None


def window_runs(fetch_page, start, end, max_pages=3):
    """Return (records, exhaustive, error), failing closed on missing pages."""
    if not 1 <= max_pages <= 20:
        raise ValueError("max_pages must be 1..20")
    found = {}
    for page in range(1, max_pages + 1):
        try:
            response = fetch_page(start, end, page)
            runs = response["workflow_runs"]
            total_count = response.get("total_count")
            if type(total_count) is not int or total_count < 0:
                raise ValueError("RUN_TOTAL_COUNT_UNVERIFIED")
            if not isinstance(runs, list):
                raise ValueError("RUNS_NOT_LIST")
            for run in runs:
                if not isinstance(run, dict) or type(run.get("id")) is not int:
                    raise ValueError("RUN_METADATA_INVALID")
                created = run.get("created_at")
                if not isinstance(created, str):
                    raise ValueError("RUN_CREATED_AT_MISSING")
                try:
                    moment = datetime.fromisoformat(created.replace("Z", "+00:00"))
                    if moment.tzinfo is None:
                        raise ValueError("NAIVE_TIME")
                except (ValueError, OverflowError) as exc:
                    raise ValueError("RUN_CREATED_AT_INVALID") from exc
                if not start <= moment <= end:
                    raise ValueError("RUN_OUTSIDE_REQUESTED_WINDOW")
                found[run["id"]] = {
                    "id": run["id"], "workflow": run.get("name"),
                    "event": run.get("event"), "status": run.get("status"),
                    "conclusion": run.get("conclusion"), "created_at": created,
                }
            if len(runs) < 100:
                if len(found) < total_count:
                    return [], False, "RUN_TOTAL_COUNT_MISMATCH"
                return sorted(found.values(), key=lambda x: (x["created_at"], x["id"])), True, None
        except (KeyError, TypeError, ValueError, OSError) as exc:
            return [], False, type(exc).__name__ + ":" + str(exc)[:120]
    return sorted(found.values(), key=lambda x: (x["created_at"], x["id"])), False, "PAGE_LIMIT_REACHED"


def audit(root, day, now, fetch_page, max_pages=3):
    """Only matured observed races with no existing snapshot are assessed."""
    if not re.fullmatch(r"20\d{6}", day):
        raise ValueError("INVALID_DAY")
    doc_path = root / "data/site_paper_sim/readiness_history_v215" / (day + ".json")
    try:
        history = json.loads(doc_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise ValueError("HISTORY_UNAVAILABLE") from exc
    if (history.get("schema") != "BOAT_EDGE_V215_DIAGNOSTIC_HISTORY_V1"
            or history.get("day_jst") != day
            or not isinstance(history.get("observations"), dict)):
        raise ValueError("HISTORY_UNVERIFIED")
    output = []
    for key, record in sorted(history["observations"].items()):
        if not (KEY.fullmatch(str(key)) and key.startswith(day + "-") and isinstance(record, dict)):
            continue
        due = deadline_for(key, record.get("deadline"))
        if due is None or now < due or (root / "data/site_prediction_snapshots" / (key + ".json")).is_file():
            continue
        start, end = due - timedelta(minutes=10), due - timedelta(minutes=2)
        runs, complete, error = window_runs(fetch_page, start.astimezone(timezone.utc),
                                            end.astimezone(timezone.utc), max_pages)
        # V125 is a valid *potential wake source* only on its independent
        # schedule. Its V229-triggered workflow_run performs index auditing
        # but must NEVER dispatch V229 back (completion feedback cycle).
        v125 = "BOAT EDGE V125 Revision Safe FINAL15M Audit"
        passive_v125_completions = sum(
            r.get("workflow") == v125 and r.get("event") == "workflow_run"
            for r in runs)
        owners = [{**r, "owner": OWNERS[r["workflow"]]} for r in runs
                  if r.get("workflow") in OWNERS and
                  (r.get("workflow") != v125 or r.get("event") == "schedule")]
        present = {r["owner"] for r in owners}
        if not complete:
            classification = "RUN_HISTORY_UNVERIFIED"
        elif "v229" in present:
            # GitHub can create a workflow_run with a skipped job. Such a
            # record is NOT evidence that the atomic first-Git writer ran.
            # Cancelled runs may have executed partially; their job execution
            # remains unverified until job-level logs are inspected.
            v229 = [r for r in owners if r["owner"] == "v229"]
            if all(r["conclusion"] == "skipped" for r in v229):
                classification = "V229_ALL_RUNS_SKIPPED_NO_EXECUTED_FREEZE_PROVEN"
            elif all(r["conclusion"] in ("skipped", "cancelled") for r in v229):
                classification = "V229_ONLY_SKIPPED_OR_CANCELLED_EXECUTION_UNVERIFIED"
            else:
                classification = "V229_START_RECORDED_SNAPSHOT_MISSING"
        elif "v216" in present:
            classification = "V216_START_WITHOUT_V229_START"
        elif "v125_schedule" in present:
            classification = "V125_SCHEDULE_STARTED_WITHOUT_V229_START"
        elif present:
            classification = "SOURCE_OR_RECOVERY_START_WITHOUT_V229_START"
        else:
            classification = "NO_CAPTURE_OWNER_START_IN_WINDOW"
        output.append({
            "race_key": key, "deadline_jst": due.strftime("%H:%M"),
            "window_start_utc": utc_string(start),
            "window_end_utc": utc_string(end),
            "run_history_complete_for_window": complete,
            "run_history_error": error,
            "all_actions_starts_in_window": len(runs),
            "capture_owner_starts": owners,
            "v229_execution_proven_by_run_metadata": False,
            "v125_completion_only_audit_starts_ignored": passive_v125_completions,
            "classification": classification,
            "observed_source_gaps": record.get("source_gaps_seen"),
            "independent_source_eligibility_proven": False,
            "no_prior_active_run_proven": False,
            "first_git_save_absent_in_current_tree": True,
        })
    return {
        "schema": "BOAT_EDGE_C1_MISSING_FREEZE_ACTIONS_WINDOW_V1",
        "day_jst": day, "read_only": True,
        "snapshot_freeze_window_minutes_before_deadline": [10, 2],
        "observed_matured_missing_snapshots": len(output),
        "complete_window_queries": sum(x["run_history_complete_for_window"] for x in output),
        "incomplete_window_queries": sum(not x["run_history_complete_for_window"] for x in output),
        "independently_source_eligible_denominator": None,
        "eligible_save_rate_percent": None,
        "automated_recovery_or_formal_unlock_authorized": False,
        "limitations": [
            "Actions created_at is a run start, not a verified completed job",
            "Skipped V229 runs do not prove a writer job executed; cancelled runs require job-level evidence",
            "An earlier active V229 may overlap a window without a new start",
            "A V125 schedule start only indicates a possible guarded V229 wake, not a dispatch",
            "V125 workflow_run completion events are passive audits, never V229 recovery attempts",
            "Empty historical source-gap observations do not prove eligibility",
            "Git source publication and per-source validity at decision time are not verified",
            "Read-only diagnosis only; never retrospectively freeze a race",
        ],
        "races": output,
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--repo", required=True)
    p.add_argument("--root", type=Path, default=Path("."))
    p.add_argument("--day", default="yesterday", help="today, yesterday, or YYYYMMDD in JST")
    p.add_argument("--max-pages", type=int, default=3)
    args = p.parse_args()
    if not re.fullmatch(r"[\w.-]+/[\w.-]+", args.repo):
        p.error("INVALID_REPOSITORY")
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if not token:
        p.error("READ_ONLY_ACTIONS_TOKEN_REQUIRED")
    now = datetime.now(timezone.utc)
    jst_today = now.astimezone(JST).date()
    day = ((jst_today - timedelta(days=1)).strftime("%Y%m%d") if args.day == "yesterday"
           else jst_today.strftime("%Y%m%d") if args.day == "today" else args.day)
    def fetch(start, end, page):
        query = urllib.parse.urlencode({
            "created": utc_string(start) + ".." + utc_string(end),
            "per_page": 100, "page": page,
        })
        url = f"https://api.github.com/repos/{args.repo}/actions/runs?{query}"
        request = urllib.request.Request(url, headers={
            "Accept": "application/vnd.github+json",
            "Authorization": "Bearer " + token,
            "User-Agent": "boat-edge-c1-readonly-window-audit",
        })
        with urllib.request.urlopen(request, timeout=20) as response:
            return json.load(response)
    print(json.dumps(audit(args.root, day, now, fetch, args.max_pages),
                     ensure_ascii=False, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
