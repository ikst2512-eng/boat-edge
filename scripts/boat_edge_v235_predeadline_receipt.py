#!/usr/bin/env python3
"""V235 read-only SITE PRE_RESULT receipt. Never accesses result or formal data.

A green Actions run is not a prediction. Require an actual newly-added Git
snapshot, the V229 audit, byte SHA and a Git commit before the race deadline.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import re
import subprocess

JST = timezone(timedelta(hours=9))
KEY = re.compile(r"^20\d{6}-\d{2}-\d{2}$")


def load(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError):
        return {}


def instant(raw):
    try:
        value = datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
        return value if value.tzinfo is not None else None
    except (TypeError, ValueError, OverflowError):
        return None


def git(root, *args):
    try:
        return subprocess.run(
            ["git", *args], cwd=root, check=True, capture_output=True,
            timeout=10,
        ).stdout
    except (OSError, subprocess.SubprocessError):
        return None


def choose(root, now, requested=None):
    date = now.astimezone(JST).strftime("%Y%m%d")
    catalog = load(root / "data/today.json")
    if str(catalog.get("date", "")).replace("-", "") != date:
        return None
    found = []
    for venue in catalog.get("venues") or []:
        for row in venue.get("races") or []:
            key = row.get("race_key")
            if not isinstance(key, str) or not KEY.fullmatch(key) or not key.startswith(date + "-"):
                continue
            clock = str(row.get("deadline") or "")
            if not re.fullmatch(r"(?:[01]\d|2[0-3]):[0-5]\d", clock):
                continue
            try:
                due = datetime.strptime(date + clock, "%Y%m%d%H:%M").replace(tzinfo=JST)
            except ValueError:
                continue
            found.append((due, key, venue.get("venue"), clock))
    if not found:
        return None
    if requested is not None:
        for item in found:
            if item[1] == requested:
                return item
        return None
    # One-day owner-requested priority; no historical or other-date guesses.
    if date == "20261014":
        for item in found:
            if item[1] == "20261014-14-01":
                return item
    upcoming = [x for x in found if x[0] >= now - timedelta(minutes=2)]
    return min(upcoming or found, key=lambda x: x[0])


def receipt(root, now=None, requested=None):
    root = Path(root)
    now = (now or datetime.now(JST)).astimezone(JST)
    record = {
        "schema": "BOAT_EDGE_V235_SITE_FIRST_GIT_RECEIPT_V1",
        "scope": "SITE_PRE_RESULT_ONLY_NOT_FORMAL_FRESH",
        "checked_at_jst": now.isoformat(),
        "results_read": False,
        "formal_unlock": False,
        "prediction_saved_proven": False,
    }
    chosen = choose(root, now, requested)
    if chosen is None:
        record["status"] = "NO_SAME_DAY_VERIFIED_RACE_ID"
        return record
    due, key, venue, clock = chosen
    left = (due - now).total_seconds() / 60
    record.update(race_key=key, venue=venue, deadline_jst=clock, minutes_to_deadline=round(left, 2))
    race = load(root / "data/races" / (key + ".json"))
    sources = race.get("source_audit") or {}
    scratch = load(root / "data/site_scratches_v182" / (key + ".json"))
    odds = load(root / "data/site_odds" / (key + ".json"))
    record["sources"] = {
        "race_card": (sources.get("race_card") or {}).get("status", "missing"),
        "beforeinfo": (sources.get("beforeinfo") or {}).get("status", "missing"),
        "scratch": "blocked" if scratch.get("blocked") is True else
                   "observed_no_signal" if scratch.get("blocked") is False else "missing",
        "odds_120_verified": (odds.get("race_key") == key and
                              odds.get("verified_official_dom_v167") is True and
                              odds.get("available_count") == 120 and
                              odds.get("phase") == "PRE_RESULT_PURCHASE_ONLY"),
    }
    status = load(root / "data/site_autopilot/v230_fast_current.json")
    if status.get("day_jst") == key[:8]:
        record["v230_targeted"] = key in (status.get("targets") or [])
        record["v230_outcome"] = (status.get("outcomes") or {}).get(key, "no_target_outcome")
    snap_path = "data/site_prediction_snapshots/" + key + ".json"
    snap_file = root / snap_path
    if not snap_file.is_file():
        record["status"] = "BEFORE_SOURCE_WINDOW" if left > 19 else (
            "SOURCE_WINDOW_NO_SNAPSHOT" if left >= 2 else "SNAPSHOT_MISSING_OR_DEADLINE_PASSED")
        return record
    raw = snap_file.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    snap = load(snap_file)
    audit = load(root / "data/site_prediction_audit" / (key + ".json"))
    record["snapshot_sha256"] = digest
    record["model_id"] = snap.get("prediction_kind", "unknown")
    record["selection_policy"] = snap.get("selection_policy", "unknown")
    record["first_saved_at"] = snap.get("first_saved_at")
    record["saved_at"] = snap.get("saved_at")
    tickets = ((snap.get("modes") or {}).get("hit") or {}).get("tickets") or []
    record["top3"] = [x.get("combo") for x in tickets[:3]]
    record["top5"] = [x.get("combo") for x in tickets[:5]]
    record["top10"] = [x.get("combo") for x in tickets[:10]]
    if (snap.get("race_key") != key or snap.get("snapshot_window") != "FINAL_15M" or
            snap.get("prediction_kind") != "SITE_REFERENCE_V122" or
            any((snap.get("guards") or {}).get(x) is not False for x in ("results_seen", "unlock", "scoring")) or
            len(tickets) < 10 or len(set(record["top10"])) != 10 or
            audit.get("latest_snapshot_sha256") != digest or audit.get("pass") is not True):
        record["status"] = "SNAPSHOT_OR_V229_AUDIT_UNVERIFIED"
        return record
    first = instant(snap.get("first_saved_at"))
    if first is None or first >= due or not 2 <= (due - first).total_seconds() / 60 <= 10:
        record["status"] = "SNAPSHOT_SAVED_OUTSIDE_DECISION_WINDOW"
        return record
    commits = git(root, "log", "--diff-filter=A", "--format=%H", "--", snap_path)
    if not commits:
        record["status"] = "LOCAL_SNAPSHOT_NOT_FIRST_GIT_COMMITTED"
        return record
    first_sha = commits.decode("utf-8", "replace").strip().splitlines()[-1]
    if not re.fullmatch(r"[a-f0-9]{40}", first_sha):
        record["status"] = "GIT_FIRST_COMMIT_UNVERIFIED"
        return record
    git_raw = git(root, "show", first_sha + ":" + snap_path)
    committed_at_raw = git(root, "show", "-s", "--format=%cI", first_sha)
    committed_at = instant(committed_at_raw.decode().strip()) if committed_at_raw else None
    record["first_git_commit"] = first_sha
    record["first_git_commit_at"] = committed_at.isoformat() if committed_at else None
    record["first_git_snapshot_sha256"] = hashlib.sha256(git_raw).hexdigest() if git_raw else None
    if (committed_at is None or committed_at >= due or
            git_raw is None or hashlib.sha256(git_raw).hexdigest() != digest):
        record["status"] = "FIRST_GIT_COMMIT_NOT_SOURCE_BOUND_PREDEADLINE"
        return record
    record["prediction_saved_proven"] = True
    record["status"] = "SITE_FIRST_GIT_COMMIT_BEFORE_DEADLINE"
    return record


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--race-key", default=None)
    args = parser.parse_args()
    value = receipt(Path(args.root), requested=args.race_key)
    print("V235_PRIORITY_PRE_RESULT_GIT_RECEIPT " + json.dumps(value, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
