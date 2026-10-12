#!/usr/bin/env python3
"""V313 official raw-byte SHA attestation, read only and pre-result only.

Verifies saved official HTML against source_audit.sha256 and recorded
pre-deadline Git revision. Does NOT authenticate upstream publication time,
GitHub first-seen time, BOATERS/競艇日和, actual entry, or predictions.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import subprocess
from urllib.parse import parse_qs, urlsplit

from boat_edge_v311_existing_source_audit import audit_race, timestamp

JST = timezone(timedelta(hours=9))
KINDS = {"race_card": ("racelist", "racelist.html"),
         "beforeinfo": ("beforeinfo", "beforeinfo.html")}


def official_url_matches(url, kind, date, venue, race):
    if not isinstance(url, str):
        return False
    parsed = urlsplit(url)
    if parsed.scheme != "https" or parsed.hostname != "www.boatrace.jp" or parsed.username or parsed.password:
        return False
    if parsed.port not in (None, 443):
        return False
    if not parsed.path.endswith("/owpc/pc/race/" + KINDS[kind][0]):
        return False
    query = parse_qs(parsed.query)
    return (query.get("hd") == [date] and query.get("jcd") == [venue]
            and query.get("rno") == [str(race)])


def last_git_commit_before(root, rel, deadline):
    """Local Git timestamp is an audit clue, NOT trusted server reception time."""
    try:
        path = rel.as_posix()
        committed = subprocess.run(
            ["git", "show", "HEAD:" + path], cwd=root,
            capture_output=True, check=True).stdout
        disk = (root / rel).read_bytes()
        if committed != disk:
            return False
        result = subprocess.run(
            ["git", "log", "-1", "--format=%cI", "--", path],
            cwd=root, capture_output=True, text=True, check=True)
        dt = timestamp(result.stdout.strip())
        return dt is not None and dt < deadline
    except (OSError, subprocess.CalledProcessError):
        return False


def verify_race(root, race):
    report = audit_race(race)
    key = report["race_key"]
    date, venue, no = key.split("-")
    deadline = timestamp(report["deadline_jst"])
    evidence = race.get("source_audit")
    evidence = evidence if isinstance(evidence, dict) else {}
    rows = {}
    for kind, (_, suffix) in KINDS.items():
        rel = Path("data") / "raw" / date / (venue + "_" + no + "_" + suffix)
        source = evidence.get(kind)
        source = source if isinstance(source, dict) else {}
        path = root / rel
        official_url = official_url_matches(source.get("source"), kind, date, venue, int(no))
        digest_match = False
        if path.is_file():
            digest_match = hashlib.sha256(path.read_bytes()).hexdigest() == source.get("sha256")
        qualified = report["source_metadata"][kind]["pre_deadline_metadata_qualified"]
        git_qualified = last_git_commit_before(root, rel, deadline) if digest_match else False
        rows[kind] = {
            "raw_path": rel.as_posix(),
            "raw_present": path.is_file(),
            "raw_sha256_matches_audit": bool(digest_match),
            "official_url_race_identity_matches": bool(official_url),
            "recorded_fetch_predeadline": bool(qualified),
            "local_git_commit_record_predeadline": bool(git_qualified),
            "evidence_bundle_consistent": bool(official_url and digest_match and qualified and git_qualified),
        }
    return {
        "race_key": key,
        "kind": "V313_OFFICIAL_RAW_BYTES_READ_ONLY",
        "official": rows,
        "boaters_raw_verified": False,
        "kyoteibiyori_raw_verified": False,
        "actual_course_verified": False,
        "github_server_received_before_deadline": False,
        "site_source_independently_authenticated": False,
        "model_promotion_authorized": False,
        "results_read": False,
        "formal_fresh_read": False,
    }


def main():
    parser = argparse.ArgumentParser(description="Audit raw official HTML vs race metadata, no results")
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--race-key", required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    source_path = root / "data" / "races" / (args.race_key + ".json")
    race = json.loads(source_path.read_text(encoding="utf-8"))
    print(json.dumps(verify_race(root, race), sort_keys=True, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
