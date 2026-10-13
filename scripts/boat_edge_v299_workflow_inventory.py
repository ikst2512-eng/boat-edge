#!/usr/bin/env python3
"""Read-only BOAT EDGE Actions schedule and write-conflict inventory.

Never downloads race results, alters source data, invokes Actions or writes git refs.
Potential writers are audit candidates, not proof of accidental duplication.
"""
from __future__ import annotations
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".github" / "workflows"
RETIRED = (
    "BOAT_EDGE_V182_SCRATCH_AND_MIDODDS.yml",
    "BOAT_EDGE_V231_BYTE_EXACT_PUBLISH.yml",
    "site-v106.yml",
    "site-v108.yml",
    "site-v104.yml",
    "site-v107.yml",
    "site-v110.yml",
    "site-v111.yml",
    "BOAT_EDGE_site-v98.yml",
    "BOAT_EDGE_site-v99.yml",
    "site-v114.yml",
    "site-v120.yml",
    "site-v124.yml",
    "site-v123.yml",
    "site-v129.yml",
    "site-v130.yml",
    "site-v131.yml",
    "site-v132.yml",
    "BOAT_EDGE_V209_AI_AUTORUN_SIM.yml",
    "BOAT_EDGE_V211_DAILY_50K_SIM.yml",
    "BOAT_EDGE_V212_PAPER_SIM_INSTALL.yml",
    "BOAT_EDGE_V213_SHADOW_ROI.yml",
    "BOAT_EDGE_V214_ODDS_ARCHIVE_SHADOW.yml",
    "site-health.yml",
    "site-recovery.yml",
    "site-v103.yml",
    # V356: dormant legacy writers and post-V133 V185 relay.
    "auto-update-5min.yml",
    "auto-update-5min 2.yml",
    "auto-update-v10.yml",
    "auto-update-v10 2.yml",
    "site-v185-trigger.yml",
    "BOAT_EDGE_V221_GUARDED_DEDUP.yml",
)
LIVE = "V235.yml"

def event_block(text: str) -> str:
    """Extract indented events for plain or quoted GitHub YAML `on` keys.

    GitHub accepts `on:`, `'on':`, and `"on":`.  Stop at the next
    top-level key, not only permissions/jobs, so later YAML does not masquerade
    as additional triggers. This remains a read-only textual inventory.
    """
    match = re.search(r"""^(?:on|'on'|"on"):[ \t]*(?:\#[^\r\n]*)?\r?\n""", text, re.M)
    if not match:
        return ""
    following = text[match.end():]
    boundary = re.search(r"""^(?:[A-Za-z_][\w-]*|'[^']+'|"[^"]+")[ \t]*:""", following, re.M)
    return following[:boundary.start()] if boundary else following

def audit(root: Path = WORKFLOWS) -> dict:
    entries = []
    for path in sorted(root.glob("*")):
        if path.suffix not in (".yml", ".yaml"):
            continue
        text = path.read_text(encoding="utf-8")
        events = event_block(text)
        cron = re.findall(r"^\s+-\s+cron:\s*['\"]?([^'\"\n#]+)", events, re.M)
        scheduled = bool(re.search(r"^  schedule:", events, re.M))
        triggers = [name for name in ("push", "pull_request", "workflow_run", "workflow_dispatch", "schedule")
                    if re.search(r"^  " + name + r":", events, re.M)]
        writable = bool(re.search(r"^\s{2}contents:\s*write\s*$", text, re.M))
        writes_main = bool(re.search(r"git\s+push\s+(?:origin\s+HEAD:main|origin\s+main|&&|$)", text, re.M))
        entries.append({
            "workflow": path.name,
            "triggers": triggers,
            "crons": [s.strip() for s in cron],
            "contents_write": writable,
            "push_main_detected": writes_main,
            "scheduled_write_candidate": scheduled and writable,
        })
    return {
        "schema": "BOAT_EDGE_01_V299_READONLY_ACTIONS_INVENTORY_V1",
        "total_workflows": len(entries),
        "scheduled": sum("schedule" in x["triggers"] for x in entries),
        "scheduled_contents_writers": sorted(x["workflow"] for x in entries if x["scheduled_write_candidate"]),
        "retired_guarded": list(RETIRED),
        "workflows": entries,
    }

def verify_retired(report: dict) -> None:
    found = {x["workflow"]: x for x in report["workflows"]}
    for name in RETIRED:
        if name not in found:
            raise AssertionError("V299_REQUIRED_RETIRED_WORKFLOW_MISSING " + name)
        actual = set(found[name]["triggers"])
        if actual != {"workflow_dispatch"}:
            raise AssertionError("V299_RETIRED_WORKFLOW_REACTIVATED " + name + ": " + repr(sorted(actual)))
    live = found.get(LIVE)
    if live is None or not {"schedule", "workflow_dispatch", "workflow_run"}.issubset(live["triggers"]):
        raise AssertionError("V299_EXPECTED_CURRENT_V235_AUTOMATION_MISSING")

if __name__ == "__main__":
    report = audit()
    verify_retired(report)
    print("V299_READONLY_ACTIONS_INVENTORY_PASS")
    print(json.dumps({
        "schema": report["schema"],
        "total_workflows": report["total_workflows"],
        "scheduled": report["scheduled"],
        "scheduled_writer_count": len(report["scheduled_contents_writers"]),
        "scheduled_contents_writers": report["scheduled_contents_writers"],
        "retired_guarded": report["retired_guarded"],
    }, sort_keys=True, ensure_ascii=False))
