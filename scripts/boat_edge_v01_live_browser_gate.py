#!/usr/bin/env python3
"""Source-only gate for running costly real browser E2E after a fresh V229 save.

Scans only today's SITE PRE_RESULT V229 receipts, snapshots and audits. Checks
the first Git add timestamp against the original deadline. Never accesses
race outcomes, payouts, formal predictions or result endpoints, and never
creates, updates or promotes a prediction.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess

JST = timezone(timedelta(hours=9))
KEY = re.compile(r"20\d{6}-\d{2}-\d{2}\Z")


def instant(value):
    try:
        d = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return d.astimezone(timezone.utc) if d.tzinfo else None
    except (TypeError, ValueError, OverflowError):
        return None


def read(path):
    if path.is_symlink() or not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError):
        return None


def first_git_add(root, path):
    relative = path.relative_to(root).as_posix()
    # This queries the first-add commit of ONE specific pre-result file,
    # not the latest result, a predicted first_saved_at or the current HEAD.
    p = subprocess.run(
        ["git", "log", "--diff-filter=A", "--format=%cI", "--", relative],
        cwd=root, capture_output=True, text=True, check=False,
    )
    if p.returncode:
        return None
    dates = [instant(x) for x in p.stdout.splitlines()]
    if not dates or any(x is None for x in dates):
        return None
    return min(dates)


def valid(saved, audit, receipt, blob, key, now, first_add):
    if not KEY.fullmatch(key) or key[:8] != now.astimezone(JST).strftime("%Y%m%d"):
        return False
    if not all(isinstance(x, dict) for x in (saved, audit, receipt)):
        return False
    if any(saved.get("guards", {}).get(k) is not False
           for k in ("results_seen", "unlock", "scoring")):
        return False
    try:
        due = datetime.strptime(
            key[:8] + str(saved["deadline"]), "%Y%m%d%H:%M"
        ).replace(tzinfo=JST).astimezone(timezone.utc)
    except (ValueError, KeyError, TypeError):
        return False
    first, at = instant(saved.get("first_saved_at")), instant(saved.get("saved_at"))
    if not first or not at or not first_add:
        return False
    # 2-10m when frozen; 2-15m still left for real browser installation.
    if not (2 * 60 <= (due-first).total_seconds() <= 10 * 60
            and 2 * 60 <= (due-now).total_seconds() <= 15 * 60
            and first <= at <= first_add <= now < due):
        return False
    digest = hashlib.sha256(blob).hexdigest()
    modes = saved.get("modes") or {}
    hit = (modes.get("hit") or {}).get("tickets") or []
    first_ten = [x.get("combo") for x in hit[:10] if isinstance(x, dict)]
    if len(first_ten) != 10 or len(set(first_ten)) != 10:
        return False
    if (saved.get("race_key") != key
            or saved.get("snapshot_window") != "FINAL_15M"
            or saved.get("prediction_kind") != "SITE_REFERENCE_V122"
            or receipt.get("schema") != "BOAT_EDGE_V229_ATOMIC_PRE_RESULT_SOURCE_EVIDENCE_V1"
            or receipt.get("scope") != "SITE_REFERENCE_ONLY_NO_FORMAL_OR_RESULT_ACCESS"
            or receipt.get("race_key") != key
            or receipt.get("snapshot_saved_at") != saved.get("saved_at")
            or receipt.get("snapshot_sha256") != digest
            or receipt.get("new_snapshot_created_this_run") is not True
            or any(receipt.get(k) is not False for k in
                   ("results_seen", "formal_fresh_unlock", "scoring"))
            or audit.get("race_key") != key or audit.get("pass") is not True
            or audit.get("latest_snapshot_sha256") != digest):
        return False
    # A populated settlement is not PRE_RESULT evidence; do not inspect it.
    if "settlement" in audit:
        return False
    return True


def candidates(root, now):
    root = Path(root).resolve()
    form = read(root / "data/formal_status.json") or {}
    flags = form.get("guards") or {}
    if (any(flags.get(k) is not False for k in
            ("results_seen", "unlock", "scoring"))
            or flags.get("RESULT_UNLOCK_TOKEN") is not None
            or (form.get("formalFirst100") or {}).get("races") != 0):
        raise ValueError("FORMAL_FRESH_CLOSED_REQUIRED")
    day = now.astimezone(JST).strftime("%Y%m%d")
    eligible = []
    directory = root / "data/site_autopilot/v229_evidence"
    for receipt_path in sorted(directory.glob(day + "-??-??.json")):
        key = receipt_path.stem
        if not KEY.fullmatch(key):
            continue
        snapshot_path = root / "data/site_prediction_snapshots" / (key + ".json")
        audit_path = root / "data/site_prediction_audit" / (key + ".json")
        if snapshot_path.is_symlink() or not snapshot_path.is_file():
            continue
        raw = snapshot_path.read_bytes()
        snapshot = read(snapshot_path)
        audit, receipt = read(audit_path), read(receipt_path)
        commit_at = first_git_add(root, snapshot_path)
        if valid(snapshot, audit, receipt, raw, key, now, commit_at):
            eligible.append({"race_key": key, "deadline": snapshot["deadline"],
                             "first_git_add_utc": commit_at.isoformat(),
                             "snapshot_sha256": hashlib.sha256(raw).hexdigest()})
    return eligible


if __name__ == "__main__":
    now = datetime.now(timezone.utc)
    checked = candidates(Path("."), now)
    output = os.environ.get("GITHUB_OUTPUT")
    if output:
        with open(output, "a", encoding="utf-8") as f:
            f.write("live_candidate=" + ("true" if checked else "false") + "\n")
    print("V01_LIVE_BROWSER_ACTUAL_PREDEADLINE_GATE " +
          json.dumps({"eligible_count": len(checked),
                      "eligible": checked[:4],
                      "browser_pass_claimed": False,
                      "formal_fresh_untouched": True},
                     ensure_ascii=False, sort_keys=True))
