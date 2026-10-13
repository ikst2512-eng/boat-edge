#!/usr/bin/env python3
"""V406: offline assembly of independently staged V402-reconciled K days.

Research-only. No network, no live/results access, no Formal Fresh, and no
license verification. This combines operator-attested normalized historical K
days; it does not authorize scraping, model training or production promotion.
Missing calendar days are UNKNOWN, not presumed to have no races.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
from collections import Counter
from datetime import datetime
from pathlib import Path

from boat_edge_v400_five_year_history_research import (
    COLUMNS, FIVE_YEAR_END_EXCLUSIVE, FIVE_YEAR_START, JST, iter_races,
    validate_manifest,
)
from boat_edge_v403_five_year_coverage_audit import _verify_day, audit as coverage_audit

MODEL = "BOAT_EDGE_V406_OFFLINE_RECONCILED_HISTORY_PACKAGE_V1"
INDEX_SCHEMA = "BOAT_EDGE_V406_LOCAL_DAY_INDEX_V1"
CUTOFF = datetime.combine(FIVE_YEAR_END_EXCLUSIVE, datetime.min.time(), JST)
DAY_FIELDS = {"source_day", "normalized_csv", "v400_manifest", "v402_report"}


def _sha(raw):
    return hashlib.sha256(raw).hexdigest()


def _stable(obj):
    return json.dumps(obj, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":")).encode("utf-8")


def package_days(days):
    """Return (normalized 5-year CSV bytes, V400 manifest, audit), offline.

    days: dicts containing source_day, k_csv bytes, k_manifest dict,
    v402_report dict. All actual K/finish/course values come only from supplied
    previously authorized local files and must match V402 reconciled evidence.
    """
    max_days = (FIVE_YEAR_END_EXCLUSIVE - FIVE_YEAR_START).days
    if not isinstance(days, list) or not 0 < len(days) <= max_days:
        raise ValueError("STAGED_DAY_LIST_REQUIRED")
    seen = set()
    day_parts = []  # compact canonical text per source day, not one dict per boat
    lineage = []
    reports = []
    for item in days:
        if not isinstance(item, dict) or set(item) != {
            "source_day", "k_csv", "k_manifest", "v402_report"
        }:
            raise ValueError("EXACT_STAGED_DAY_FIELDS_REQUIRED")
        day_text = item["source_day"]
        raw, manifest, report = (
            item["k_csv"], item["k_manifest"], item["v402_report"]
        )
        if not isinstance(raw, bytes) or not isinstance(manifest, dict):
            raise ValueError("STAGED_CSV_BYTES_AND_MANIFEST_REQUIRED")
        report_day = _verify_day(report)
        if not isinstance(day_text, str) or day_text != report_day.isoformat():
            raise ValueError("INDEX_V402_DAY_MISMATCH")
        if report_day in seen:
            raise ValueError("DUPLICATE_STAGED_DAY")
        seen.add(report_day)
        validate_manifest(manifest, raw, CUTOFF)
        if report["k_normalized_sha256"] != _sha(raw):
            raise ValueError("V402_K_CSV_SHA_MISMATCH")
        try:
            source = raw.decode("utf-8-sig")
        except UnicodeError as exc:
            raise ValueError("STAGED_HISTORY_UTF8_REQUIRED") from exc
        race_count = 0
        by_venue = Counter()
        day_output = io.StringIO(newline="")
        day_writer = csv.DictWriter(day_output, fieldnames=COLUMNS,
                                    lineterminator="\n")
        for race in iter_races(source, CUTOFF):
            if race[0][1] != report_day:
                raise ValueError("STAGED_CSV_SOURCE_DAY_MISMATCH")
            race_count += 1
            by_venue[f"{race[0][2]:02d}"] += 1
            for entry in race:
                day_writer.writerow({
                    "race_key": entry[0], "boat": str(entry[3]),
                    "racer_id": entry[4],
                    "actual_course": str(entry[5]),
                    "finish": str(entry[6]),
                    "published_at": entry[7].isoformat(),
                })
        if race_count != report["reconciled_six_boat_races"]:
            raise ValueError("V402_K_RACE_TOTAL_MISMATCH")
        expected_by_venue = {
            venue: info["k_complete_races"]
            for venue, info in report["by_venue"].items()
            if info["k_complete_races"]
        }
        if dict(by_venue) != expected_by_venue:
            raise ValueError("V402_K_VENUE_COUNTS_MISMATCH")
        day_parts.append((day_text, day_output.getvalue()))
        reports.append(report)
        lineage.append({
            "source_day": day_text,
            "normalized_k_sha256": _sha(raw),
            "v400_manifest_sha256": _sha(_stable(manifest)),
            "v402_report_sha256": _sha(_stable(report)),
            "included_races": race_count,
            "excluded_races": report["excluded_with_explicit_reason"],
        })

    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=COLUMNS, lineterminator="\n")
    writer.writeheader()
    for _, text_rows in sorted(day_parts):
        output.write(text_rows)
    combined_raw = output.getvalue().encode("utf-8")
    # Revalidate the merged six-entry permutation and ordering, not just days.
    if sum(1 for _ in iter_races(combined_raw.decode("utf-8"), CUTOFF)) != sum(
        r["reconciled_six_boat_races"] for r in reports
    ):
        raise AssertionError("MERGED_K_RACE_COUNT_DRIFT")
    lineage.sort(key=lambda r: r["source_day"])
    lineage_sha = _sha(_stable(lineage))
    manifest = {
        "schema": "BOAT_EDGE_V400_STAGED_HISTORY_MANIFEST_V1",
        "csv_sha256": _sha(combined_raw),
        "source_name": "V406_OPERATOR_STAGED_K_B_RECONCILED",
        "source_locator": "offline:lineage-sha256:" + lineage_sha,
        "rights_evidence": "Self-attested on each input V400 source manifest; "
                           "rights not independently authenticated; see audit",
        "rights_review_status": "OPERATOR_REVIEWED_OFFLINE_RESEARCH_ONLY",
        "normalization_protocol": MODEL,
    }
    validate_manifest(manifest, combined_raw, CUTOFF)
    coverage = coverage_audit(reports)
    race_total = sum(r["reconciled_six_boat_races"] for r in reports)
    return combined_raw, manifest, {
        "schema": MODEL,
        "research_only": True,
        "input_days": len(days),
        "normalized_complete_races": race_total,
        "normalized_six_boat_rows": race_total * 6,
        "history_csv_sha256": _sha(combined_raw),
        "lineage_sha256": lineage_sha,
        "source_lineage": lineage,
        "coverage": coverage,
        "calendar_coverage_complete": coverage["calendar_coverage_complete"],
        "historic_source_rights_independently_verified": False,
        "historic_publication_timestamps_independently_verified": False,
        "historical_b_roster_predeadline_capture_verified": False,
        "results_downloaded_by_this_script": False,
        "formal_fresh_read": False,
        "accuracy_improvement_proven": False,
        "production_model_changed": False,
        "model_promotion_authorized": False,
        "wagers_authorized": False,
    }


def _read_local(root, name):
    if (not isinstance(name, str) or not name or
            Path(name).is_absolute() or ".." in Path(name).parts):
        raise ValueError("UNSAFE_STAGE_RELATIVE_PATH")
    path = (root / name).resolve()
    if not path.is_relative_to(root) or not path.is_file():
        raise ValueError("STAGE_FILE_MISSING_OR_OUTSIDE_ROOT")
    return path.read_bytes()


def stage_from_index(root, index):
    """Read explicit local paths ONLY; cannot fetch a URL or browse a result API."""
    if not isinstance(index, dict) or set(index) != {"schema", "days"}:
        raise ValueError("EXACT_LOCAL_INDEX_REQUIRED")
    if index["schema"] != INDEX_SCHEMA or not isinstance(index["days"], list):
        raise ValueError("INVALID_LOCAL_INDEX_SCHEMA")
    days = []
    for item in index["days"]:
        if not isinstance(item, dict) or set(item) != DAY_FIELDS:
            raise ValueError("EXACT_LOCAL_DAY_INDEX_FIELDS")
        raw = _read_local(root, item["normalized_csv"])
        man = json.loads(_read_local(root, item["v400_manifest"]).decode("utf-8"))
        report = json.loads(_read_local(root, item["v402_report"]).decode("utf-8"))
        days.append({
            "source_day": item["source_day"], "k_csv": raw,
            "k_manifest": man, "v402_report": report,
        })
    return days


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--staging-dir", type=Path, required=True,
                        help="Pre-authorized local stage, NOT any website/API")
    parser.add_argument("--index-json", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True,
                        help="Private offline output; NEVER commit real K data")
    args = parser.parse_args()
    root = args.staging_dir.resolve(strict=True)
    raw, manifest, audit = package_days(stage_from_index(
        root, json.loads(args.index_json.read_text(encoding="utf-8"))
    ))
    dest = args.output_dir.resolve()
    if dest == root or root in dest.parents:
        raise ValueError("OUTPUT_MUST_NOT_OVERWRITE_STAGING_TREE")
    dest.mkdir(parents=True, exist_ok=True)
    (dest / "history.csv").write_bytes(raw)
    (dest / "history.manifest.json").write_bytes(_stable(manifest) + b"\n")
    (dest / "history.audit.json").write_bytes(_stable(audit) + b"\n")
    print(json.dumps({
        "csv_sha256": audit["history_csv_sha256"],
        "lineage_sha256": audit["lineage_sha256"],
        "complete_races": audit["normalized_complete_races"],
        "missing_calendar_days": audit["coverage"]["days_without_verified_v402_reports"],
        "rights_independently_verified": False,
        "production_model_changed": False
    }, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
