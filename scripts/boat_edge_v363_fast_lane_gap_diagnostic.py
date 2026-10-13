#!/usr/bin/env python3
"""V363: read-only explanation of an upstream V230 fast-lane skip condition.

V230 targets() excludes races with existing site_prediction_snapshots.
V336 is independently interested in their current 15-minute research window.
This classifier reads only V361 selection-time diagnostics and an existence
check on that site-only snapshot path. It is NOT a source refresh, eligibility
override, outcome reader, workflow scheduler or assertion of cause.
"""
from __future__ import annotations

from pathlib import Path

MODEL = "BOAT_EDGE_V363_SITE_RESEARCH_UPSTREAM_REFRESH_DIAG_ONLY"
RACE_STALE = "SOURCE_SCAN_STALE:race_card"
BEFOREINFO_STALE = "SOURCE_SCAN_STALE:beforeinfo"
SOURCE_NOT_OK = {"SOURCE_NOT_OK:race_card", "SOURCE_NOT_OK:beforeinfo"}


def classify(root, scan):
    if not isinstance(scan, dict) or scan.get("preflight_can_authorize_freeze") is not False:
        raise ValueError("V363_UNTRUSTED_READ_ONLY_SCAN")
    key = scan.get("race_key")
    if (not isinstance(key, str) or len(key) != 14 or
            scan.get("results_read") is not False or
            scan.get("formal_fresh_read") is not False):
        raise ValueError("V363_INVALID_RESEARCH_SCAN")
    issues = scan.get("issues")
    if not isinstance(issues, list) or any(not isinstance(x, str) for x in issues):
        raise ValueError("V363_INVALID_ISSUES")
    root = Path(root).resolve()
    target = root / "data/site_prediction_snapshots" / (key + ".json")
    # Do not open, hash or inspect the existing independent SITE prediction.
    # A symlink is still an existing path and V230's target filter also skips
    # it if it resolves to a file; explicitly identify that case as unknown.
    snapshot_regular = target.is_file() and not target.is_symlink()
    symlink = target.is_symlink()
    race_card_needs_refresh = any(x in issues for x in (
        RACE_STALE, "SOURCE_NOT_OK:race_card",
        "SOURCE_SCAN_TIMESTAMP_UNKNOWN:race_card",
        "SOURCE_SCAN_TIMESTAMP_FUTURE:race_card",
    ))
    beforeinfo_needs_refresh = any(x in issues for x in (
        BEFOREINFO_STALE, "SOURCE_NOT_OK:beforeinfo",
        "SOURCE_SCAN_TIMESTAMP_UNKNOWN:beforeinfo",
        "SOURCE_SCAN_TIMESTAMP_FUTURE:beforeinfo",
    ))
    return {
        "model_id": MODEL,
        "race_key": key,
        "site_prediction_snapshot_exists_as_regular_file": snapshot_regular,
        "site_prediction_snapshot_is_symlink_not_read": symlink,
        "v230_existing_snapshot_filter_applies_if_same_checkout": snapshot_regular,
        "race_card_refresh_needed_from_selection_metadata": race_card_needs_refresh,
        "beforeinfo_refresh_needed_from_selection_metadata": beforeinfo_needs_refresh,
        "potential_v230_fast_lane_snapshot_refresh_gap":
            snapshot_regular and (race_card_needs_refresh or beforeinfo_needs_refresh),
        "source_refresh_performed": False,
        "refresh_gap_cause_independently_proven": False,
        "source_read_or_authenticated": False,
        "site_prediction_snapshot_opened": False,
        "preflight_can_authorize_freeze": False,
        "formal_fresh_read": False,
        "results_read": False,
        "writes_performed": False,
    }
