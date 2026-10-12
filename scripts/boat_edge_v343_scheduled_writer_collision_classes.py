#!/usr/bin/env python3
"""V343 read-only classification of V341 *candidate* staging-path collisions.

Literal git-add paths are not evidence of concurrent writes or duplicate bytes.
Dynamic staging remains unresolved. No workflow runs, GitHub API, race data,
Formal Fresh, or outcome material is inspected.
"""
from __future__ import annotations

import json
from pathlib import Path

try:
    from scripts.boat_edge_v341_scheduled_writer_path_audit import audit as v341_audit
except ModuleNotFoundError:
    from boat_edge_v341_scheduled_writer_path_audit import audit as v341_audit

EXACT = "EXACT_PATH"
LEFT_PARENT = "LEFT_PARENT_OF_RIGHT"
RIGHT_PARENT = "RIGHT_PARENT_OF_LEFT"


def path_relation(left: str, right: str) -> str | None:
    """Require a directory boundary, not merely a shared string prefix."""
    if left == right:
        return EXACT
    if right.startswith(left + "/"):
        return LEFT_PARENT
    if left.startswith(right + "/"):
        return RIGHT_PARENT
    return None


def classify_pair(left_paths: list[str], right_paths: list[str]) -> dict | None:
    exact, parent = [], []
    for left in sorted(set(left_paths)):
        for right in sorted(set(right_paths)):
            relation = path_relation(left, right)
            if relation is None:
                continue
            witness = {"left": left, "right": right, "relation": relation}
            (exact if relation == EXACT else parent).append(witness)
    if not (exact or parent):
        return None
    category = ("MIXED_EXACT_AND_PARENT" if exact and parent else
                "EXACT_ONLY" if exact else "PARENT_CHILD_ONLY")
    return {
        "classification": category,
        "exact_path_witness_count": len(exact),
        "parent_directory_witness_count": len(parent),
        "exact_path_witnesses_first_12": exact[:12],
        "parent_directory_witnesses_first_12": parent[:12],
        "exact_witnesses_truncated": len(exact) > 12,
        "parent_witnesses_truncated": len(parent) > 12,
    }


def audit(root: Path | None = None) -> dict:
    old = v341_audit() if root is None else v341_audit(root)
    records = old["scheduled_candidate_records"]
    classified = []
    counts = {"EXACT_ONLY": 0, "PARENT_CHILD_ONLY": 0, "MIXED_EXACT_AND_PARENT": 0}
    for index, left in enumerate(records):
        for right in records[index + 1:]:
            relationship = classify_pair(left["staged_literals"], right["staged_literals"])
            if relationship is None:
                continue
            counts[relationship["classification"]] += 1
            classified.append({"left": left["workflow"], "right": right["workflow"], **relationship})
    if len(classified) != old["candidate_overlapping_workflow_pairs"]:
        raise ValueError("V341_OVERLAP_COUNT_CHANGED_DURING_CLASSIFICATION")
    return {
        "schema": "BOAT_EDGE_01_V343_STATIC_STAGING_PATH_CLASSES_V1",
        "read_only": True,
        "verified_duplicate_writers": 0,
        "classification_does_not_authorize_workflow_disable": True,
        "results_or_formal_data_read": False,
        "base_v341_schema": old["schema"],
        "workflow_files_scanned": old["workflow_files_scanned"],
        "scheduled_contents_write_candidates": old["scheduled_contents_write_candidates"],
        "candidates_with_no_literal_staging_path": old["candidates_with_no_literal_staging_path"],
        "candidates_with_unresolved_staging": old["candidates_with_unresolved_staging"],
        "candidate_overlapping_workflow_pairs": len(classified),
        "pair_class_counts": counts,
        "exact_path_witness_count": sum(x["exact_path_witness_count"] for x in classified),
        "parent_directory_witness_count": sum(x["parent_directory_witness_count"] for x in classified),
        "classified_pairs_first_100": classified[:100],
        "classified_pairs_truncated": len(classified) > 100,
        "all_classifications_are_candidates_not_proof": True,
    }


if __name__ == "__main__":
    print(json.dumps(audit(), ensure_ascii=False, sort_keys=True, indent=2))
