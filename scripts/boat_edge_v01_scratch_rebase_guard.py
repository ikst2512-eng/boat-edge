#!/usr/bin/env python3
"""Read-only fail-closed check before preserving remote scratch evidence on rebase.

During the rolling PRE_RESULT collector push, V186 may have independently
updated the same V182 scratch file. Rebase's 'ours' is the *remote* Git version.
Never overwrite it with an older local observation; also never suppress a
local explicit withdrawal in favour of a remote false/green scratch verdict.

This tool reads Git's staged conflict blobs only. No races/results/payouts or
formal prediction data are read, and no file is modified.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

JST = timezone(timedelta(hours=9))
import json
from pathlib import Path
import re
import subprocess
import sys

SCRATCH_PATH = re.compile(r"data/site_scratches_v182/(20\d{6}-\d{2}-\d{2})\.json\Z")
CONFIRMED_PATH = re.compile(r"(?:data/races/20\d{6}-\d{2}-\d{2}\.json|data/raw/20\d{6}/\d{2}_\d{2}_(?:racelist|beforeinfo)\.html)\Z")
SUSPICIOUS = re.compile(r"欠場|出走取消|出走取り消し|取消|不出走|欠航|scratched|withdrawn", re.I)


class UnsafeConflict(ValueError):
    pass


def timestamp(v):
    try:
        d = datetime.fromisoformat(str(v).replace("Z", "+00:00"))
        return d.astimezone(timezone.utc) if d.tzinfo else None
    except (TypeError, ValueError, OverflowError):
        return None


def safe_remote_scratch(path: str, remote: dict, local: dict, now: datetime) -> bool:
    """True authorizes *remote-wins only*, not a new verified prediction."""
    m = SCRATCH_PATH.fullmatch(path)
    if not m or not isinstance(remote, dict) or not isinstance(local, dict):
        return False
    key = m.group(1)
    day = key[:8]
    if day != now.astimezone(JST).strftime("%Y%m%d"):
        return False
    for item in (remote, local):
        if (item.get("schema_version") != "boat-edge-v182-scratch-evidence-v1"
                or item.get("race_key") != key or item.get("source_date") != day
                or type(item.get("blocked")) is not bool):
            return False
        checked = timestamp(item.get("checked_at"))
        if checked is None or checked > now:
            return False
    # A local withdrawal is never silently hidden behind a remote green state.
    local_suspicious = (local["blocked"] is True or bool(local.get("suspect_lanes"))
                        or bool(local.get("official_raw_flags"))
                        or bool(SUSPICIOUS.search(str(local.get("reason") or ""))))
    if local_suspicious and remote["blocked"] is False:
        return False
    if remote["blocked"] is False:
        # The remote record is not a new GREEN attestation by this script:
        # ensure local also green with six-boat official data and no flags.
        if (local["blocked"] is not False
                or remote.get("race_card_source_status") != "ok"
                or remote.get("official_beforeinfo_source_status") != "ok"
                or local.get("race_card_source_status") != "ok"
                or local.get("official_beforeinfo_source_status") != "ok"
                or local.get("official_beforeinfo_six_boat_complete") is not True
                or remote.get("suspect_lanes") or remote.get("official_raw_flags")):
            return False
    return True


def git_blob(path: str, stage: int, root: Path) -> dict:
    r = subprocess.run(["git", "show", f":{stage}:{path}"], cwd=root,
                       capture_output=True, check=False)
    if r.returncode:
        raise UnsafeConflict("V01_SCRATCH_CONFLICT_STAGE_MISSING")
    try:
        obj = json.loads(r.stdout.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise UnsafeConflict("V01_SCRATCH_CONFLICT_BAD_JSON") from exc
    if not isinstance(obj, dict):
        raise UnsafeConflict("V01_SCRATCH_CONFLICT_BAD_OBJECT")
    return obj


def audit(root: Path, paths: list[str], now: datetime) -> list[str]:
    if not paths:
        raise UnsafeConflict("V01_NO_CONFLICT_INPUT")
    if now.tzinfo is None:
        raise UnsafeConflict("V01_TIMEZONE_REQUIRED")
    allowed = []
    for path in paths:
        if not isinstance(path, str) or path.startswith("/") or ".." in Path(path).parts:
            raise UnsafeConflict("V01_UNSAFE_PATH")
        if CONFIRMED_PATH.fullmatch(path):
            allowed.append(path)  # old remote-preservation behavior unchanged
            continue
        if SCRATCH_PATH.fullmatch(path):
            remote = git_blob(path, 2, root)  # --ours in a rebase is origin/main
            local = git_blob(path, 3, root)
            if not safe_remote_scratch(path, remote, local, now):
                raise UnsafeConflict("V01_SCRATCH_SOURCE_CONFLICT_REQUIRES_RETRY_" + path)
            allowed.append(path)
            continue
        raise UnsafeConflict("V01_UNRELATED_CONFLICT_REFUSED_" + path)
    return allowed


if __name__ == "__main__":
    try:
        files = sys.argv[1:]
        permitted = audit(Path("."), files, datetime.now(timezone.utc))
    except UnsafeConflict as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1)
    print("V01_REMOTE_SCRATCH_CONFLICT_SAFELY_PRESERVED", len(permitted))
