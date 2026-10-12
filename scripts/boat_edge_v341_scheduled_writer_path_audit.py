#!/usr/bin/env python3
"""V341 read-only staging-path overlap audit for scheduled BOAT EDGE Actions.

This is a conservative inventory of *literal git-add arguments*, not proof
that two workflows write identical bytes, run concurrently, or cause a race.
It never executes workflow contents, accesses race records or uses the network.
"""
from __future__ import annotations

import json
from pathlib import Path
import re
import shlex

try:
    from scripts.boat_edge_v299_workflow_inventory import WORKFLOWS, audit as workflow_audit
except ModuleNotFoundError:
    from boat_edge_v299_workflow_inventory import WORKFLOWS, audit as workflow_audit

ADD = re.compile(r"(?<![\w-])git[ \t]+add[ \t]+([^\n\r]+)")
BREAK = {"||", "&&", ";", "|", "fi", "then", "done"}
FLAGS = {"-A", "--all", "-u", "--update", "--ignore-removal", "--"}
ROOT = Path(__file__).resolve().parents[1]


def _arguments(line: str) -> tuple[list[str], bool]:
    paths: list[str] = []
    dynamic = False
    for match in ADD.finditer(line):
        try:
            words = shlex.split(match.group(1).split("#", 1)[0], posix=True)
        except ValueError:
            dynamic = True
            continue
        for word in words:
            if word in BREAK or word.startswith((";", "&&", "||")):
                break
            if word in FLAGS:
                continue
            if word.startswith("-") or word.startswith("$") or any(c in word for c in "*?{}"):
                dynamic = True
                continue
            if word.startswith(("../", "/", "~/")) or "/../" in word or word.endswith("/.."):
                dynamic = True
                continue
            path = word.removeprefix("./").rstrip("/")
            if not path or path == ".":
                dynamic = True
                continue
            if re.fullmatch(r"[A-Za-z0-9_.\-/]+", path):
                paths.append(path)
            else:
                dynamic = True
    return sorted(set(paths)), dynamic


def staged_paths(text: str) -> tuple[list[str], bool]:
    result: set[str] = set()
    unresolved = False
    for line in text.splitlines():
        if not ADD.search(line):
            continue
        paths, dynamic = _arguments(line)
        result.update(paths)
        unresolved |= dynamic
    return sorted(result), unresolved


def _overlap(a: str, b: str) -> bool:
    return a == b or a.startswith(b + "/") or b.startswith(a + "/")


def audit(root: Path = WORKFLOWS) -> dict:
    report = workflow_audit(root)
    records: list[dict] = []
    for entry in report["workflows"]:
        if not entry["scheduled_write_candidate"]:
            continue
        path = root / entry["workflow"]
        paths, dynamic = staged_paths(path.read_text(encoding="utf-8"))
        records.append({
            "workflow": entry["workflow"],
            "crons": entry["crons"],
            "staged_literals": paths,
            "unresolved_staging_arguments": dynamic,
            "literal_path_detection_only": True,
        })
    pairs: list[dict] = []
    for i, left in enumerate(records):
        for right in records[i + 1:]:
            overlaps = sorted({
                (a, b) for a in left["staged_literals"]
                for b in right["staged_literals"] if _overlap(a, b)
            })
            if overlaps:
                pairs.append({
                    "left": left["workflow"],
                    "right": right["workflow"],
                    "staging_path_witnesses": [
                        {"left": a, "right": b} for a, b in overlaps[:12]
                    ],
                    "witnesses_truncated": len(overlaps) > 12,
                })
    return {
        "schema": "BOAT_EDGE_01_V341_STATIC_STAGING_PATH_OVERLAP_V1",
        "read_only": True,
        "verified_duplicate_writers": 0,
        "overlap_is_only_candidate_not_proof": True,
        "results_or_formal_data_read": False,
        "workflow_files_scanned": report["total_workflows"],
        "scheduled_contents_write_candidates": len(records),
        "candidates_with_no_literal_staging_path": sum(
            not item["staged_literals"] for item in records
        ),
        "candidates_with_unresolved_staging": sum(
            item["unresolved_staging_arguments"] for item in records
        ),
        "candidate_overlapping_workflow_pairs": len(pairs),
        "overlap_pairs_first_100": pairs[:100],
        "pairs_output_truncated": len(pairs) > 100,
        "scheduled_candidate_records": records,
    }


if __name__ == "__main__":
    print(json.dumps(audit(), sort_keys=True, ensure_ascii=False, indent=2))
