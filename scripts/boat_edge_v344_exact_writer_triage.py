#!/usr/bin/env python3
"""V344: deterministic, read-only exact-path candidate triage.

No workflow execution, disablement, result endpoints or race data access.
"""
import json
from pathlib import Path
try:
    from scripts.boat_edge_v343_scheduled_writer_collision_classes import audit as v343_audit
except ModuleNotFoundError:
    from boat_edge_v343_scheduled_writer_collision_classes import audit as v343_audit


def triage(root: Path | None = None):
    prior = v343_audit(root)
    exact = []
    for pair in prior["classified_pairs_first_100"]:
        for witness in pair["exact_path_witnesses_first_12"]:
            exact.append({
                "left": pair["left"],
                "right": pair["right"],
                "path": witness["left"],
                "status": "UNVERIFIED_SAME_LITERAL_STAGING_PATH",
                "owner": "UNRESOLVED",
                "disable_authorized": False,
            })
    if prior["classified_pairs_truncated"] or any(
        p["exact_witnesses_truncated"] for p in prior["classified_pairs_first_100"]
    ):
        raise ValueError("TRIAGE_REQUIRES_COMPLETE_EXACT_WITNESSES")
    exact.sort(key=lambda x: (x["path"], x["left"], x["right"]))
    if len(exact) != prior["exact_path_witness_count"]:
        raise ValueError("EXACT_WITNESS_COUNT_MISMATCH")
    return {
        "schema": "BOAT_EDGE_01_V344_EXACT_PATH_CANDIDATE_TRIAGE_V1",
        "read_only": True,
        "classification_source": prior["schema"],
        "exact_only_pairs": prior["pair_class_counts"]["EXACT_ONLY"],
        "exact_witness_count": len(exact),
        "verified_duplicate_writers": 0,
        "unresolved_dynamic_staging_workflows": prior["candidates_with_unresolved_staging"],
        "candidates": exact,
        "no_disable_or_owner_transfer_authorized": True,
        "next_proof_needed": "Compare concrete generated output paths, triggering conditions and run timestamps before assigning ownership",
    }


if __name__ == "__main__":
    print(json.dumps(triage(), ensure_ascii=False, sort_keys=True, indent=2))
