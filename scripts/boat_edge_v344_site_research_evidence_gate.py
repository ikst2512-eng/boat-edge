#!/usr/bin/env python3
"""One offline gate for explicitly supplied SITE research artifact bundles.

Combines V339 cross-run collisions, V340 frozen/source-byte integrity and V343
exact candidate replay. Never fetches or scores outcomes, discovers artifacts,
repairs missing evidence or authorizes Formal Fresh or model promotion.
"""
from __future__ import annotations

import argparse
from datetime import datetime
import json
from pathlib import Path

from boat_edge_v339_cross_run_research_audit import _check_report, audit as collision_audit
from boat_edge_v340_artifact_integrity import audit as byte_audit
from boat_edge_v343_race_input_replay import verify as replay_audit

MODEL = "BOAT_EDGE_V344_SITE_RESEARCH_LOCAL_EVIDENCE_GATE"


def check(bundles):
    if not isinstance(bundles, list) or not bundles:
        raise ValueError("EXPLICIT_NONEMPTY_BUNDLE_LIST_REQUIRED")
    reports = []
    # Validate every report before any artifact read. Each selected race must
    # have either a completion or an explicit failure; omissions hide attrition.
    for item in bundles:
        if not isinstance(item, dict) or set(item) != {"root", "report"}:
            raise ValueError("EXPLICIT_ROOT_REPORT_PAIR_REQUIRED")
        report = item["report"]
        validated = _check_report(report, len(reports) + 1)
        try:
            datetime.strptime(validated["date"], "%Y%m%d")
        except ValueError as exc:
            raise ValueError("VALID_CALENDAR_DATE_REQUIRED") from exc
        if validated["selected"] != validated["completed"] + validated["failed"]:
            raise ValueError("UNACCOUNTED_SELECTED_RACES")
        if report.get("immutable_across_independent_actions_runs_verified") is not False:
            raise ValueError("NO_UNVERIFIED_GLOBAL_IMMUTABILITY_CLAIM")
        reports.append(report)
    collisions = collision_audit(reports)
    audits, rejected = [], []
    for index, item in enumerate(bundles, 1):
        root, report = Path(item["root"]), item["report"]
        local = byte_audit(root, report)
        row = {"bundle_index": index, "source_bytes": local}
        if local["local_artifacts_rejected"]:
            rejected.append({"bundle_index": index, "stage": "SOURCE_BYTES",
                             "reasons": local["rejected"]})
        try:
            row["candidate_replay"] = replay_audit(root, report)
        except (OSError, UnicodeError, ValueError, TypeError, KeyError) as exc:
            rejected.append({"bundle_index": index, "stage": "CANDIDATE_REPLAY",
                             "reason": str(exc)})
        audits.append(row)
    count = collisions["total_local_freezes_across_reports"]
    failures = collisions["total_failed_attempts_across_reports"]
    divergent = collisions["cross_run_divergent_sha_race_count"]
    repeated = collisions["cross_run_repeat_race_count"]
    passed = count > 0 and not (failures or divergent or repeated or rejected)
    if divergent:
        status = "DIVERGENT_REPEATED_FREEZES"
    elif repeated:
        status = "REPEATED_RACES_NOT_UNIQUE"
    elif rejected:
        status = "LOCAL_ARTIFACT_EVIDENCE_REJECTED"
    elif not count:
        status = "NO_RESEARCH_FREEZES_TO_VERIFY"
    elif failures:
        status = "REPORTED_CAPTURE_FAILURES_PREVENT_COMPLETE_BATCH_PASS"
    else:
        status = "LOCAL_EVIDENCE_CHECKS_PASSED_NOT_FORMAL"
    full120 = [row["candidate_replay"].get("all_supplied_full_120_verified", False)
               for row in audits if "candidate_replay" in row]
    return {
        "model_id": MODEL, "status": status,
        "all_supplied_full_120_rankings_replayed": bool(audits) and len(full120) == len(audits) and all(full120),
        "all_supplied_local_evidence_checks_passed": passed,
        "supplied_bundle_count": len(bundles),
        "completed_attempts": count, "reported_capture_failures": failures,
        "distinct_frozen_races_in_supplied_reports": collisions[
            "distinct_frozen_race_keys_within_supplied_reports"],
        "cross_run_collisions": collisions,
        "bundle_checks": audits, "rejected": rejected,
        "complete_actions_history_or_global_uniqueness_attested": False,
        "capture_timestamps_independently_authenticated": False,
        "upstream_source_identity_or_fields_authenticated": False,
        "independent_actual_entry_verified": False,
        "formal_fresh_read": False, "results_read": False,
        "scoring_authorized": False, "accuracy_improvement_proven": False,
        "production_model_changed": False, "model_promotion_authorized": False,
        "wagers_authorized": False, "writes_performed": False,
    }


def main():
    parser = argparse.ArgumentParser(description="Check explicit SITE research bundles, no outcome access")
    parser.add_argument("--bundle", nargs=2, action="append", required=True,
                        metavar=("ARTIFACT_ROOT", "RUN_REPORT"))
    args = parser.parse_args()
    bundles = [{"root": root, "report": json.loads(Path(report).read_text(encoding="utf-8"))}
               for root, report in args.bundle]
    result = check(bundles)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2))
    # A zero/failure/duplicate batch must not look successful to automation.
    if not result["all_supplied_local_evidence_checks_passed"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
