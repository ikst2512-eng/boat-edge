#!/usr/bin/env python3
"""V347 read-only runtime evidence validation; no API calls or workflow changes.

Only explicit independently sourced run/commit evidence can raise proof coverage.
No duplicate-writer verdict is made automatically.
"""
from __future__ import annotations
import json
from pathlib import Path
try:
    from scripts.boat_edge_v346_runtime_proof_gate import audit as v346_audit
except ModuleNotFoundError:
    from boat_edge_v346_runtime_proof_gate import audit as v346_audit

REQUIRED = ("workflow", "run_id", "started_at", "completed_at", "commit_sha", "changed_paths")


def validate_records(records: list[dict]) -> dict:
    accepted, rejected = [], []
    for i, row in enumerate(records):
        missing = [k for k in REQUIRED if k not in row or row[k] in (None, "", [])]
        if not missing and (not isinstance(row["run_id"], int) or isinstance(row["run_id"], bool) or row["run_id"] <= 0):
            missing.append("run_id_valid")
        if not missing and (not isinstance(row["changed_paths"], list) or
                            not all(isinstance(x, str) and x for x in row["changed_paths"])):
            missing.append("changed_paths_valid")
        if missing:
            rejected.append({"index": i, "missing_or_invalid": missing})
        else:
            accepted.append(row)
    return {"accepted": accepted, "rejected": rejected}


def audit(records: list[dict] | None = None, root: Path | None = None) -> dict:
    baseline = v346_audit() if root is None else v346_audit(root)
    validated = validate_records([] if records is None else records)
    return {
        "schema": "BOAT_EDGE_01_V347_RUNTIME_EVIDENCE_INTAKE_V1",
        "read_only": True,
        "static_candidate_count": baseline["static_candidate_count"],
        "run_records_supplied": len(records or []),
        "valid_run_records": len(validated["accepted"]),
        "rejected_records": validated["rejected"],
        "verified_duplicate_writers": 0,
        "workflow_disable_authorized": False,
        "runtime_pair_proof_not_implemented": True,
        "missing_run_records_are_not_zero_collisions": True,
        "provenance_required": "Record original Actions run URL, workflow identity and commit evidence separately before manual review",
    }


if __name__ == "__main__":
    print(json.dumps(audit(), ensure_ascii=False, sort_keys=True, indent=2))
