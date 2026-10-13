#!/usr/bin/env python3
"""V136 historical SITE-only V125 proof: immutable first Git bytes, no results read.

The V125 index.json is regenerated for *today*. Historical settled SITE rows
must use their own race-scoped V125 receipt instead of today's empty index.
No previous/current outcome endpoint or formal Fresh asset is consulted.
"""
from datetime import datetime, timedelta, timezone
from pathlib import Path
import hashlib
import json
import re
import subprocess

JST = timezone(timedelta(hours=9))
RACE_KEY = re.compile(r"20\d{6}-\d{2}-\d{2}\Z")
CLOCK = re.compile(r"(?:[01]\d|2[0-3]):[0-5]\d\Z")
SHA256 = re.compile(r"[0-9a-f]{64}\Z")


def _parse_instant(value):
    try:
        t = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return t.astimezone(timezone.utc) if t.tzinfo is not None else None
    except (ValueError, TypeError, OverflowError):
        return None


def check_historical_proof(root, key, snap):
    """Return (PASS|reason, first_git_commit). Fail closed on any missing proof."""
    root = Path(root)
    if not isinstance(key, str) or not RACE_KEY.fullmatch(key):
        return "invalid_race_key", None
    if snap.get("race_key") != key:
        return "history_race_identity_mismatch", None
    clock = snap.get("deadline")
    if not isinstance(clock, str) or not CLOCK.fullmatch(clock):
        return "race_deadline_unverified", None
    try:
        due = datetime.strptime(key[:8] + clock, "%Y%m%d%H:%M").replace(tzinfo=JST)
    except ValueError:
        return "race_deadline_unverified", None
    first = _parse_instant(snap.get("first_saved_at"))
    saved = _parse_instant(snap.get("saved_at"))
    if first is None or saved is None or not first <= saved < due:
        return "history_time_not_predeadline", None

    relative = f"data/site_prediction_snapshots/{key}.json"
    path = root / relative
    audit_path = root / "data/site_prediction_audit" / f"{key}.json"
    try:
        source = path.read_bytes()
        audit = json.loads(audit_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError):
        return "historical_v125_or_snapshot_missing", None
    digest = hashlib.sha256(source).hexdigest()
    if (audit.get("schema_version") != "boat-edge-final15m-audit-v125"
            or audit.get("race_key") != key or audit.get("pass") is not True
            or audit.get("latest_snapshot_saved_at") != snap.get("saved_at")
            or audit.get("latest_snapshot_sha256") != digest):
        return "historical_v125_receipt_mismatch", None
    revisions = audit.get("revisions")
    if not isinstance(revisions, list) or not revisions:
        return "historical_v125_revision_missing", None
    matches = [row for row in revisions if isinstance(row, dict)
               and row.get("snapshot_sha256") == digest
               and row.get("saved_at") == snap["saved_at"]
               and row.get("first_saved_at") == snap["first_saved_at"]
               and row.get("prediction_kind") == snap.get("prediction_kind")]
    if len(matches) != 1:
        return "historical_v125_revision_mismatch", None
    flags = matches[0].get("intrinsic_flags")
    if not isinstance(flags, dict) or not flags or any(v is not True for v in flags.values()):
        return "historical_v125_intrinsic_unverified", None
    if not SHA256.fullmatch(digest):
        return "historical_sha256_invalid", None
    try:
        history = subprocess.run(
            ["git", "-C", str(root), "log", "--diff-filter=A",
             "--format=%H%x09%cI", "--", relative],
            capture_output=True, text=True, check=True, timeout=12,
        ).stdout.strip().splitlines()
        # A re-created path or ambiguous first-add history is not immutable proof.
        if len(history) != 1:
            return "first_git_add_missing_or_ambiguous", None
        sha, committed = history[0].split("\t", 1)
        if re.fullmatch(r"[0-9a-f]{40}", sha) is None:
            return "first_git_commit_invalid", None
        at = _parse_instant(committed)
        if at is None or at >= due.astimezone(timezone.utc) or at > datetime.now(timezone.utc) + timedelta(seconds=60):
            return "first_git_commit_not_predeadline", None
        # Git only stores seconds; the 1s tolerance is for first_saved_at micros.
        if at + timedelta(seconds=1) < first:
            return "first_git_commit_before_snapshot", None
        original = subprocess.run(
            ["git", "-C", str(root), "show", f"{sha}:{relative}"],
            capture_output=True, check=True, timeout=12,
        ).stdout
    except (OSError, ValueError, subprocess.SubprocessError):
        return "first_git_provenance_unverified", None
    if hashlib.sha256(original).hexdigest() != digest:
        return "first_git_snapshot_bytes_mismatch", None
    try:
        original_snap = json.loads(original)
    except (ValueError, UnicodeError):
        return "first_git_snapshot_unreadable", None
    if (original_snap.get("race_key") != key
            or original_snap.get("saved_at") != snap.get("saved_at")
            or original_snap.get("first_saved_at") != snap.get("first_saved_at")
            or original_snap.get("guards") != {"results_seen": False,
                                                 "unlock": False, "scoring": False}):
        return "first_git_snapshot_metadata_mismatch", None
    return "PASS", sha
