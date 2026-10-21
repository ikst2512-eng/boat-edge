#!/usr/bin/env python3
"""Read-only C-1 drop-off triage. Never infer eligibility from an absence of evidence.

Inputs are JSON reports from boat_edge_c1_observed_audit.py and
boat_edge_01_gate1c_actions_window_audit.py for the SAME JST day.
No production data is mutated. These categories are investigative leads,
not a certified denominator or proof of an eligible save failure.
"""
import argparse
import json
from collections import Counter
from pathlib import Path

SCHEMA = "BOAT_EDGE_C1_DROPOFF_TRIAGE_V1"


def classify(observed, actions):
    if observed.get("day_jst") != actions.get("day_jst"):
        raise ValueError("DAY_MISMATCH")
    if observed.get("schema") != "BOAT_EDGE_C1_OBSERVED_FIRST_GIT_ACCOUNTING_V1":
        raise ValueError("OBSERVED_SCHEMA_INVALID")
    if actions.get("schema") != "BOAT_EDGE_C1_MISSING_FREEZE_ACTIONS_WINDOW_V1":
        raise ValueError("ACTIONS_SCHEMA_INVALID")
    observed_rows = {r["race_key"]: r for r in observed["races"]}
    action_rows = {r["race_key"]: r for r in actions["races"]}
    output = []
    for key in sorted(set(observed_rows) | set(action_rows)):
        o, a = observed_rows.get(key, {}), action_rows.get(key, {})
        status = o.get("status")
        source = o.get("latest_source_timing") or {}
        sources = source.get("sources") or {}
        gap = o.get("source_gaps_at_last_observation") or []
        if status == "PROVEN_FIRST_GIT_BEFORE_DEADLINE":
            stage = "FIRST_GIT_RECEIPT_PROVEN"
        elif status == "PENDING_BEFORE_DEADLINE":
            stage = "PENDING_NOT_FAILURE"
        elif status == "UNKNOWN_DEADLINE":
            stage = "DEADLINE_UNVERIFIED"
        elif a and not a.get("run_history_complete_for_window"):
            stage = "ACTIONS_HISTORY_INCOMPLETE"
        elif a and a.get("classification") == "V229_START_RECORDED_SNAPSHOT_MISSING":
            stage = "V229_STARTED_WRITE_OR_INPUT_UNRESOLVED"
        elif a and "SKIPPED_OR_CANCELLED" in a.get("classification", ""):
            stage = "V229_EXECUTION_UNVERIFIED"
        elif a and a.get("classification") == "V229_ALL_RUNS_SKIPPED_NO_EXECUTED_FREEZE_PROVEN":
            stage = "V229_JOB_NOT_EXECUTED"
        elif gap or any(v.get("latest_file_verified") is False for v in sources.values()):
            stage = "SOURCE_GAP_SUSPECTED_NOT_HISTORICALLY_PROVEN"
        elif a and a.get("classification") == "NO_NEW_CAPTURE_OWNER_START_PRIOR_ACTIVE_RUN_UNVERIFIED":
            stage = "SCHEDULER_OR_PRIOR_RUN_UNVERIFIED"
        elif a:
            stage = "PREDICTION_GATE_OR_FREEZE_UNRESOLVED"
        else:
            stage = "INSUFFICIENT_EVIDENCE"
        output.append({
            "race_key": key, "stage": stage,
            "observation_status": status or "NOT_IN_OBSERVATION_REPORT",
            "receipt_status": o.get("receipt_status"),
            "actions_classification": a.get("classification"),
            "source_gaps_observed": gap,
            "historic_source_eligibility_proven": False,
            "first_git_save_failure_proven": False,
            "sha_lineage_verified": False,
            "next_check": (
                "Compare immutable source bytes/timestamps, prediction inputs, "
                "first Git-add receipt, V229 job logs and push outcome at the same decision instant."
            ),
        })
    return {
        "schema": SCHEMA, "day_jst": observed["day_jst"],
        "scope": "INVESTIGATIVE_TRIAGE_NOT_FORMAL_ELIGIBILITY",
        "observed_rows": len(observed_rows), "actions_missing_rows": len(action_rows),
        "union_rows": len(output),
        "stage_counts": dict(sorted(Counter(r["stage"] for r in output).items())),
        "independently_source_eligible_denominator": None,
        "formal_save_rate_percent": None,
        "c1_passed": False,
        "limitations": [
            "Latest mutable source files are not immutable historic evidence.",
            "Actions run starts cannot prove V229 job completion or successful Git push.",
            "Source SHA and prediction input SHA lineage remain unverified.",
            "Missing observed races are not automatically ineligible or missed saves.",
        ],
        "races": output,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--observed", required=True, type=Path)
    parser.add_argument("--actions", required=True, type=Path)
    args = parser.parse_args()
    observed = json.loads(args.observed.read_text(encoding="utf-8"))
    actions = json.loads(args.actions.read_text(encoding="utf-8"))
    print(json.dumps(classify(observed, actions), ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
