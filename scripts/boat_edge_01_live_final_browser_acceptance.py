#!/usr/bin/env python3
"""01 Pages acceptance: distinguish real immutable FINAL TopK from navigation-only PASS.

The existing V01 first-Git-add source gate chooses when browser execution
is eligible. This script only validates its real read-only Chromium/WebKit
browser report. It never fetches race outcomes or changes any prediction.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import re
import sys

CERTIFIED = "VERIFIED_SAVED_FINAL_TOP3_TOP5_TOP10_SHA_PARITY"
PAGES = "https://ikst2512-eng.github.io/boat-edge/index.html"
KEY = re.compile(r"20\d{6}-\d{2}-\d{2}\Z")


class GateError(ValueError):
    pass


def verify_browser_log(path: Path, engine: str) -> dict:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError) as exc:
        raise GateError("PUBLISHED_BROWSER_LOG_MISSING") from exc
    prefix = "BOAT_EDGE_03_REAL_BROWSER_PASS "
    reports = [line.partition(prefix)[2] for line in lines if prefix in line]
    if len(reports) != 1:
        raise GateError("PUBLISHED_BROWSER_REPORT_COUNT_INVALID")
    try:
        report = json.loads(reports[0])
    except (TypeError, ValueError) as exc:
        raise GateError("PUBLISHED_BROWSER_REPORT_BAD_JSON") from exc
    live = report.get("live_topk") or {}
    if (report.get("browser") != engine
            or report.get("target") != PAGES
            or live.get("status") != CERTIFIED
            or live.get("verified_site_final") is not True
            or live.get("displayed_matches_saved_selected_mode") is not True
            or (live.get("saved_prediction") or {}).get("first_git_commit_verified") is not False
            or not KEY.fullmatch(str(live.get("race") or ""))
            or report.get("physical_iphone_safari_verified") is not False
            or report.get("result_requests_allowed") != 0
            or report.get("formal_fresh_modified") is not False
            or report.get("page_errors")):
        raise GateError("PUBLISHED_SAVED_FINAL_TOPK_NOT_CERTIFIED_" + engine)
    return {"browser": engine, "race": live["race"], "status": CERTIFIED}


def verify_both(chromium: Path, webkit: Path) -> str:
    left = verify_browser_log(chromium, "chromium")
    right = verify_browser_log(webkit, "webkit")
    if left["race"] != right["race"]:
        raise GateError("PUBLISHED_BROWSERS_SHOW_DIFFERENT_SAVED_FINAL_RACES")
    return left["race"]


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--chromium", type=Path, required=True)
    parser.add_argument("--webkit", type=Path, required=True)
    opt = parser.parse_args()
    try:
        print("PUBLISHED_SAVED_FINAL_TOP3_TOP5_TOP10_BOTH_BROWSERS_PASS",
              verify_both(opt.chromium, opt.webkit))
    except GateError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1)
