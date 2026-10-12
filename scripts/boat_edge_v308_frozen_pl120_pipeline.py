#!/usr/bin/env python3
"""V308 offline pre-result -> actual-course -> 120-way research pipeline.

Only explicitly source-verified, deadline-frozen six-boat strength records.
No network, result, payout, odds, formal data, or production writes.
"""
import argparse
import json
from pathlib import Path

from boat_edge_v307_pre_result_adapter import provenance_digest, validated_course_strengths
from boat_edge_v307_pl120_research import research_report, rank_120
from boat_edge_v317_ticket_mapper import map_course_mass_to_boat_tickets

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
    # A user-supplied source_verified boolean is not independent verification.
    report["actual_course_verified"] = False
    report["actual_course_permutation_supplied"] = True
    report["source_authentication_independent"] = False
    report["boat_ticket_research_only"] = map_course_mass_to_boat_tickets(
        rank_120(strengths),
        {int(boat): course for boat, course in record["actual_course_by_boat"].items()},
        "ACTUAL_ENTRY_ASSERTED_NOT_AUTHENTICATED",
    )
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
