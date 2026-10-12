#!/usr/bin/env python3
"""Read-only BOAT EDGE master-TODO status audit; never access formal result sources."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


def load_json(root: Path, path: str) -> dict | None:
    try:
        obj = json.loads((root / path).read_text(encoding="utf-8"))
        return obj if isinstance(obj, dict) else None
    except (OSError, ValueError):
        return None


def check(root: Path) -> dict:
    """Use only site status artifacts. Never look up race results, payouts or APIs."""
    formal = load_json(root, "data/formal_status.json")
    model = load_json(root, "data/model_status.json")
    state = load_json(root, "data/site_current_state.json")
    policy = load_json(root, "data/site_prediction_policy.json")
    comparison = load_json(root, "data/site_autopilot/v236_score_current.json")
    paper = load_json(root, "data/site_paper_sim/current.json")
    try:
        queue = (root / "BOAT_EDGE_AUTODEV_TASKS.md").read_text(encoding="utf-8")
    except OSError:
        queue = None

    guards = (formal or {}).get("guards") or {}
    formal_lock = (
        isinstance(formal, dict)
        and all(guards.get(k) is False for k in ("results_seen", "unlock", "scoring"))
        and guards.get("RESULT_UNLOCK_TOKEN", "MISSING") is None
    )
    first100 = (formal or {}).get("formalFirst100") or {}
    formal_count = first100.get("races")
    if not isinstance(formal_count, int) or isinstance(formal_count, bool) or formal_count < 0:
        formal_count = None

    site_age = (state or {}).get("as_of")
    formal_age = (formal or {}).get("asOf")
    formal_date = formal_age[:10] if isinstance(formal_age, str) else None
    site_date = site_age[:10] if isinstance(site_age, str) else None

    pending = None if queue is None else re.findall(r"^- \[ \] (A\d+) \|", queue, re.MULTILINE)
    research_safe = (
        isinstance(comparison, dict)
        and comparison.get("production_model_changed") is False
        and comparison.get("promotion_authorized") is False
        and comparison.get("scope") == "POST_RESULT_SAME_COHORT_COMPARISON_NOT_FORMAL_FRESH"
    )
    paper_safe = (
        isinstance(paper, dict)
        and paper.get("mode") == "PAPER_ONLY"
        and (paper.get("money") or {}).get("virtual_only") is True
    )
    weights_safe = (
        isinstance(policy, dict)
        and policy.get("ticket_policy", {}).get("odds_rank_weight") is False
    )
    results = {
        "formal_lock": "PASS" if formal_lock else "BLOCK",
        "formal_first100": formal_count,
        "formal_freeze": (
            "UNVERIFIED" if formal_count is None else
            "WAITING_0_OF_100" if formal_count == 0 else "REQUIRES_INDEPENDENT_EVIDENCE"
        ),
        "site_status_freshness": (
            "UNVERIFIED" if not formal_date or not site_date else
            "STALE_SITE_SNAPSHOT" if site_date < formal_date else "DATE_ALIGNED"
        ),
        "site_snapshot_date": site_date,
        "formal_status_date": formal_date,
        "autodev_task_queue": (
            "UNVERIFIED" if pending is None else
            "EMPTY" if not pending else "PENDING"
        ),
        "autodev_pending_tasks": pending,
        "site_research_promotion_guard": "PASS" if research_safe else "BLOCK_OR_UNVERIFIED",
        "paper_only_guard": "PASS" if paper_safe else "BLOCK_OR_UNVERIFIED",
        "odds_not_rank_weight": "PASS" if weights_safe else "BLOCK_OR_UNVERIFIED",
        "site_full_120_distribution": (
            "NOT_CERTIFIED" if not isinstance(policy, dict) else
            "READY_CLAIM_REQUIRES_AUDIT" if policy.get("site_reference_120way_full_distribution_ready") is True
            else "NOT_READY"
        ),
        "model_status_present": isinstance(model, dict),
    }
    dangerous = (
        results["formal_lock"] != "PASS"
        or results["site_research_promotion_guard"] != "PASS"
        or results["paper_only_guard"] != "PASS"
        or results["odds_not_rank_weight"] != "PASS"
    )
    return {
        "schema": "BOAT_EDGE_MASTER_TODO_READ_ONLY_AUDIT_V1",
        "scope": "STATUS_ONLY_NO_FORMAL_RESULTS_NO_PAYOUTS_NO_NETWORK",
        "safe_to_claim_complete": False,
        "status": "SAFETY_BLOCK" if dangerous else "SAFETY_GUARDS_OBSERVED_NOT_COMPLETION",
        "checks": results,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    report = check(args.root)
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 2 if report["status"] == "SAFETY_BLOCK" else 0


if __name__ == "__main__":
    raise SystemExit(main())
