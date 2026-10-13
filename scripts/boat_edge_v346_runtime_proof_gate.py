#!/usr/bin/env python3
"""V346: fail-closed runtime proof gate for scheduled-writer candidates.

Never infer duplicate writes from staging paths or cron overlap. External run
evidence is not supplied by the static workflow inventory.
"""
import json
from pathlib import Path
try:
    from scripts.boat_edge_v345_writer_trigger_evidence import audit as v345_audit
    from scripts.boat_edge_v341_scheduled_writer_path_audit import WORKFLOWS
except ModuleNotFoundError:
    from boat_edge_v345_writer_trigger_evidence import audit as v345_audit
    from boat_edge_v341_scheduled_writer_path_audit import WORKFLOWS


def audit(root: Path = WORKFLOWS):
    previous = v345_audit(root)
    rows = []
    for c in previous["candidates"]:
        rows.append({
            "left": c["left"],
            "right": c["right"],
            "path": c["path"],
            "shared_cron_witness": bool(c["shared_literal_crons"]),
            "runtime_runs_inspected": False,
            "concurrent_run_overlap_proven": False,
            "generated_output_path_proven": False,
            "same_output_write_proven": False,
            "status": "RUNTIME_EVIDENCE_NOT_COLLECTED",
            "disable_authorized": False,
        })
    return {
        "schema": "BOAT_EDGE_01_V346_RUNTIME_DUPLICATE_PROOF_GATE_V1",
        "read_only": True,
        "static_candidate_count": len(rows),
        "verified_duplicate_writers": 0,
        "runtime_evidence_coverage": 0,
        "runtime_proof_missing": True,
        "workflow_disable_authorized": False,
        "required_external_evidence": [
            "workflow_run_ids_and_time_intervals",
            "resolved_generated_output_paths",
            "actual_write_or_commit_evidence_for_both_workflows",
        ],
        "candidates": rows,
    }


if __name__ == "__main__":
    print(json.dumps(audit(), ensure_ascii=False, sort_keys=True, indent=2))
