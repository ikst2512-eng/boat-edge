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
DIGEST = re.compile(r"[0-9a-f]{64}\Z")


class GateError(ValueError):
    pass


def parse_first_add_proofs(value: str) -> dict[str, str]:
    """Read only evidence emitted by the independently checked Git-first-add gate."""
    if not isinstance(value, str) or not value or len(value) > 20000:
        raise GateError("GIT_FIRST_ADD_RACE_SHA_PROOFS_MISSING")
    out = {}
    for item in value.split(","):
        parts = item.split(":")
        if (len(parts) != 2 or not KEY.fullmatch(parts[0])
                or not DIGEST.fullmatch(parts[1])
                or parts[0] in out):
            raise GateError("GIT_FIRST_ADD_RACE_SHA_PROOFS_INVALID")
        out[parts[0]] = parts[1]
    return out


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
    saved = live.get("saved_prediction") or {}
    if (report.get("browser") != engine
            or report.get("target") != PAGES
            or live.get("status") != CERTIFIED
            or live.get("verified_site_final") is not True
            or live.get("displayed_matches_saved_selected_mode") is not True
            or saved.get("first_git_commit_verified") is not False
            or saved.get("status") != "SITE_SNAPSHOT_SHA_V229_AUDIT_VERIFIED_GIT_UNCHECKED"
            or not DIGEST.fullmatch(str(saved.get("snapshot_sha256") or ""))
            or not KEY.fullmatch(str(live.get("race") or ""))
            or report.get("physical_iphone_safari_verified") is not False
            or report.get("result_requests_allowed") != 0
            or report.get("formal_fresh_modified") is not False
            or report.get("page_errors")):
        raise GateError("PUBLISHED_SAVED_FINAL_TOPK_NOT_CERTIFIED_" + engine)
    return {"browser": engine, "race": live["race"],
            "snapshot_sha256": saved["snapshot_sha256"], "status": CERTIFIED}


def verify_both(chromium: Path, webkit: Path, first_add_proofs: str) -> str:
    proofs = parse_first_add_proofs(first_add_proofs)
    left = verify_browser_log(chromium, "chromium")
    right = verify_browser_log(webkit, "webkit")
    if left["race"] != right["race"]:
        raise GateError("PUBLISHED_BROWSERS_SHOW_DIFFERENT_SAVED_FINAL_RACES")
    if left["snapshot_sha256"] != right["snapshot_sha256"]:
        raise GateError("PUBLISHED_BROWSERS_SHOW_DIFFERENT_SAVED_FINAL_SHA")
    if proofs.get(left["race"]) != left["snapshot_sha256"]:
        raise GateError("PUBLISHED_FINAL_NOT_SAME_RACE_SHA_AS_FIRST_GIT_ADD")
    return left["race"]


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--chromium", type=Path, required=True)
    parser.add_argument("--webkit", type=Path, required=True)
    parser.add_argument("--first-add-proofs", required=True,
                        help="Same-run predeadline Git first-add race:SHA receipts")
    opt = parser.parse_args()
    try:
        print("PUBLISHED_SAVED_FINAL_TOP3_TOP5_TOP10_BOTH_BROWSERS_PASS",
              verify_both(opt.chromium, opt.webkit, opt.first_add_proofs))
    except GateError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1)
