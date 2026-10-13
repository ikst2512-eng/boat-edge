#!/usr/bin/env python3
"""V345 read-only exact-path candidate trigger and command evidence.

Cron equality is only a scheduling hint; commands are literal textual witnesses.
No execution or verified duplicate-write claim.
"""
import json
import re
from pathlib import Path
try:
    from scripts.boat_edge_v344_exact_writer_triage import triage
    from scripts.boat_edge_v341_scheduled_writer_path_audit import WORKFLOWS
    from scripts.boat_edge_v299_workflow_inventory import audit as inventory
except ModuleNotFoundError:
    from boat_edge_v344_exact_writer_triage import triage
    from boat_edge_v341_scheduled_writer_path_audit import WORKFLOWS
    from boat_edge_v299_workflow_inventory import audit as inventory


def audit(root: Path = WORKFLOWS):
    base = triage(root)
    inv = inventory(root)
    by_name = {x["workflow"]: x for x in inv["workflows"]}
    records = []
    for candidate in base["candidates"]:
        left, right = candidate["left"], candidate["right"]
        a, b = by_name[left], by_name[right]
        path = candidate["path"]
        command_lines = {}
        for name in (left, right):
            lines = (root / name).read_text(encoding="utf-8").splitlines()
            command_lines[name] = [
                {"line": i, "text": line.strip()[:240]}
                for i, line in enumerate(lines, 1)
                if ("git add " in line and (path in line or path.split("/")[0] in line))
            ][:10]
        records.append({
            **candidate,
            "left_crons": a["crons"],
            "right_crons": b["crons"],
            "shared_literal_crons": sorted(set(a["crons"]) & set(b["crons"])),
            "left_triggers": a["triggers"],
            "right_triggers": b["triggers"],
            "git_add_line_evidence": command_lines,
            "verified_runtime_write_collision": False,
            "classification": "NEEDS_GENERATED_OUTPUT_AND_RUN_PROOF",
        })
    return {
        "schema": "BOAT_EDGE_01_V345_EXACT_PATH_TRIGGER_EVIDENCE_V1",
        "read_only": True,
        "candidate_count": len(records),
        "shared_cron_witnesses": sum(bool(x["shared_literal_crons"]) for x in records),
        "verified_duplicate_writers": 0,
        "no_disable_authorized": True,
        "candidates": records,
    }


if __name__ == "__main__":
    print(json.dumps(audit(), ensure_ascii=False, sort_keys=True, indent=2))
