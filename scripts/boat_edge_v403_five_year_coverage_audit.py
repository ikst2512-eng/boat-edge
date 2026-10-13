#!/usr/bin/env python3
"""V403: five-year historical B/K evidence coverage; offline and research-only.

Only consumes *already audited* V402 daily summaries. It does not assume 288
races/day or that an absent day necessarily had a race. Unsubmitted days are
UNKNOWN, never silently classified as no-race days. V402 summaries themselves
do not independently prove source authenticity, licensing or full daily roster.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path

from boat_edge_v400_five_year_history_research import (
    FIVE_YEAR_START as START, FIVE_YEAR_END_EXCLUSIVE as END,
)
from boat_edge_v402_offline_b_k_reconciliation import MODEL as V402

MODEL = "BOAT_EDGE_V403_FIVE_YEAR_COVERAGE_AUDIT_RESEARCH_V1"
SHA = re.compile(r"[0-9a-f]{64}\Z")
VENUES = tuple(f"{i:02d}" for i in range(1, 25))
UNPROVEN = (
    "b_program_historic_capture_independently_authenticated",
    "k_post_deadline_publication_times_independently_authenticated",
    "national_daily_coverage_independently_verified",
    "license_independently_verified",
    "formal_fresh_read", "results_downloaded_by_this_script",
    "trained_model_created", "accuracy_improvement_proven",
    "production_model_changed", "model_promotion_authorized", "wagers_authorized",
)


def _nonnegative_number(value):
    return type(value) is int and value >= 0


def _verify_day(report):
    if not isinstance(report, dict) or report.get("schema") != V402:
        raise ValueError("V402_EVIDENCE_REQUIRED")
    if report.get("research_only") is not True or any(
        report.get(flag) is not False for flag in UNPROVEN
    ):
        raise ValueError("V402_RESEARCH_ISOLATION_REQUIRED")
    if report.get("b_k_staged_race_universe_reconciled") is not True:
        raise ValueError("V402_RACE_UNIVERSE_NOT_RECONCILED")
    try:
        day = date.fromisoformat(report["source_day"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("V402_DATE_INVALID") from exc
    if not START <= day < END or day.isoformat() != report.get("source_day"):
        raise ValueError("PROTECTED_OR_OUTSIDE_FIVE_YEAR_DATE")
    for k in ("k_normalized_sha256", "b_original_sha256", "b_staged_sha256"):
        value = report.get(k)
        if not isinstance(value, str) or SHA.fullmatch(value) is None:
            raise ValueError("V402_DIGEST_INVALID:" + k)
    b, k, excluded = (report.get(field) for field in (
        "b_program_races_supplied", "reconciled_six_boat_races",
        "excluded_with_explicit_reason",
    ))
    if not all(_nonnegative_number(v) for v in (b, k, excluded)):
        raise ValueError("V402_INVALID_RACE_TOTALS")
    if b != k + excluded or b <= 0 or k <= 0:
        raise ValueError("V402_RACE_COUNTS_INCONSISTENT")
    by_venue = report.get("by_venue")
    if not isinstance(by_venue, dict) or not by_venue:
        raise ValueError("V402_VENUE_BREAKDOWN_MISSING")
    sums = [0, 0, 0]
    for venue, info in by_venue.items():
        if venue not in VENUES or not isinstance(info, dict) or set(info) != {
            "b_program_races", "k_complete_races", "excluded_races",
        }:
            raise ValueError("V402_VENUE_BREAKDOWN_INVALID")
        numbers = [info["b_program_races"], info["k_complete_races"],
                   info["excluded_races"]]
        if not all(_nonnegative_number(v) for v in numbers):
            raise ValueError("V402_VENUE_COUNTS_INVALID")
        if numbers[0] != numbers[1] + numbers[2] or numbers[0] <= 0:
            raise ValueError("V402_VENUE_COUNTS_INCONSISTENT")
        sums = [x + y for x, y in zip(sums, numbers)]
    if sums != [b, k, excluded]:
        raise ValueError("V402_VENUE_TOTALS_MISMATCH")
    return day


def _missing_spans(submitted):
    spans = []
    start = None
    last = None
    day = START
    while day < END:
        if day not in submitted:
            if start is None:
                start = day
            last = day
        elif start is not None:
            spans.append({"from": start.isoformat(), "through": last.isoformat(),
                          "days": (last - start).days + 1})
            start = None
            last = None
        day += timedelta(days=1)
    if start is not None:
        spans.append({"from": start.isoformat(), "through": last.isoformat(),
                      "days": (last - start).days + 1})
    return spans


def audit(reports):
    if not isinstance(reports, list) or len(reports) > (END - START).days:
        raise ValueError("V402_REPORT_ARRAY_REQUIRED")
    seen = set()
    venue_stats = {venue: {"reported_race_days": 0, "program_races": 0,
                           "complete_races": 0, "excluded_races": 0}
                   for venue in VENUES}
    years = {str(year): {"days_with_report": 0, "program_races": 0,
                         "complete_races": 0, "excluded_races": 0}
             for year in range(START.year, END.year + 1)}
    lineage = []
    for report in reports:
        day = _verify_day(report)
        if day in seen:
            raise ValueError("DUPLICATE_DAY_REPORT")
        seen.add(day)
        v = years[str(day.year)]
        v["days_with_report"] += 1
        for src, dst in (("b_program_races_supplied", "program_races"),
                         ("reconciled_six_boat_races", "complete_races"),
                         ("excluded_with_explicit_reason", "excluded_races")):
            v[dst] += report[src]
        for venue, counts in report["by_venue"].items():
            totals = venue_stats[venue]
            totals["reported_race_days"] += 1
            totals["program_races"] += counts["b_program_races"]
            totals["complete_races"] += counts["k_complete_races"]
            totals["excluded_races"] += counts["excluded_races"]
        lineage.append({
            "source_day": day.isoformat(),
            "b_original_sha256": report["b_original_sha256"],
            "k_normalized_sha256": report["k_normalized_sha256"],
        })
    spans = _missing_spans(seen)
    total_days = (END - START).days
    missing = sum(x["days"] for x in spans)
    if missing != total_days - len(seen):
        raise AssertionError("INCOMPLETE_CALENDAR_PARTITION")
    return {
        "schema": MODEL, "research_only": True,
        "history_start": START.isoformat(),
        "history_end_inclusive": (END - timedelta(days=1)).isoformat(),
        "calendar_days": total_days, "days_with_v402_reports": len(seen),
        "days_without_verified_v402_reports": missing,
        "unknown_or_unsubmitted_calendar_ranges": spans,
        "annual_counts": {y: v for y, v in years.items()
                          if int(y) <= END.year},
        "venue_counts": venue_stats,
        "report_lineage": sorted(lineage, key=lambda x: x["source_day"]),
        "calendar_coverage_complete": missing == 0,
        "historical_race_coverage_independently_verified": False,
        "venue_schedule_independently_verified": False,
        "source_licensing_independently_verified": False,
        "historical_results_downloaded": False,
        "formal_fresh_read": False, "trained_model_created": False,
        "accuracy_improvement_proven": False,
        "production_model_changed": False, "model_promotion_authorized": False,
        "wagers_authorized": False,
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--reports-json", type=Path, required=True,
                   help="List of V402 daily summaries, no raw results")
    a = p.parse_args()
    reports = json.loads(a.reports_json.read_text(encoding="utf-8"))
    print(json.dumps(audit(reports), ensure_ascii=False, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
