#!/usr/bin/env python3
"""V309 read-only readiness audit: no results, no inferred source trust.

This audit does not certify source authenticity. It only checks that required
provenance fields exist and flags externally asserted trust for independent review.
"""
import argparse
import json
from pathlib import Path

from boat_edge_v307_pre_result_adapter import validated_course_strengths
from boat_edge_v308_frozen_pl120_pipeline import build_report


def audit(records):
    if not isinstance(records, list):
        raise ValueError("RECORDS_MUST_BE_LIST")
    seen = set()
    accepted = []
    rejected = []
    for index, record in enumerate(records):
        key = record.get("race_key") if isinstance(record, dict) else None
        try:
            validated_course_strengths(record)
            if key in seen:
                raise ValueError("DUPLICATE_RACE_KEY")
            seen.add(key)
            report = build_report(record)
            accepted.append({"race_key": key, "top10": report["top10"],
                             "provenance_sha256": report["pre_result_provenance_sha256"],
                             "external_source_authentication": "NOT_INDEPENDENTLY_VERIFIED"})
        except (ValueError, TypeError, KeyError, OverflowError) as exc:
            rejected.append({"index": index, "race_key": key, "reason": str(exc)})
    return {"model_id": "BOAT_EDGE_V309_RESEARCH_READINESS_AUDIT",
            "input_count": len(records), "accepted_count": len(accepted),
            "rejected_count": len(rejected), "accepted": accepted,
            "rejected": rejected, "independent_source_authentication": False,
            "real_world_accuracy_evaluated": False, "production_eligible": False,
            "formal_results_read": False}


def main():
    parser = argparse.ArgumentParser(description="Offline pre-result readiness audit")
    parser.add_argument("--input", type=Path, required=True)
    args = parser.parse_args()
    records = json.loads(args.input.read_text(encoding="utf-8"))
    print(json.dumps(audit(records), ensure_ascii=False, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
