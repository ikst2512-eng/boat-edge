#!/usr/bin/env python3
"""V308 offline pre-result -> actual-course -> 120-way research pipeline.

Only explicitly source-verified, deadline-frozen six-boat strength records.
No network, result, payout, odds, formal data, or production writes.
"""
import argparse
import json
from pathlib import Path

from boat_edge_v307_pre_result_adapter import provenance_digest, validated_course_strengths
from boat_edge_v307_pl120_research import research_report

MODEL = "BOAT_EDGE_V308_FROZEN_SOURCE_PL120_RESEARCH"


def build_report(record):
    strengths = validated_course_strengths(record)
    report = research_report(strengths)
    report["pipeline_model_id"] = MODEL
    report["race_key"] = record["race_key"]
    report["source_sha256"] = record["source_sha256"]
    report["pre_result_provenance_sha256"] = provenance_digest(record)
    report["frozen_at_jst"] = record["frozen_at_jst"]
    report["deadline_jst"] = record["deadline_jst"]
    report["source_verified"] = True
    report["strength_origin"] = "EXTERNAL_VERIFIED_PRE_RESULT_ONLY"
    report["actual_course_verified"] = True
    report["production_eligible"] = False
    return report


def main():
    parser = argparse.ArgumentParser(description="V308 research only; no result inputs")
    parser.add_argument("--input", required=True, type=Path)
    args = parser.parse_args()
    record = json.loads(args.input.read_text(encoding="utf-8"))
    print(json.dumps(build_report(record), ensure_ascii=False, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
