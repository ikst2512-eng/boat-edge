#!/usr/bin/env python3
"""V277: fail-closed gate BEFORE the PRE_RESULT collector pushes a Git commit.

V275 protects sources already frozen when collection begins. This gate closes
the concurrency gap where another workflow freezes a race *during* collection.
Check only path names / formal control flags; NEVER read results, payouts, or
the contents of an existing frozen prediction.
"""
from __future__ import annotations

import json
from pathlib import Path
import re
import subprocess
import sys

RACE_SOURCE = re.compile(r"^data/races/(20\d{6}-\d{2}-\d{2})\.json$")
RAW_SOURCE = re.compile(
    r"^data/raw/(20\d{6})/(\d{2})_(\d{2})_(?:racelist|beforeinfo)\.html$"
)
FROZEN_PREFIX = "data/site_prediction_snapshots/"
FROZEN = re.compile(r"^data/site_prediction_snapshots/(20\d{6}-\d{2}-\d{2})\.json$")


class GuardFailure(RuntimeError):
    pass


def git(root: Path, *args: str) -> str:
    run = subprocess.run(
        ["git", *args], cwd=root, capture_output=True, text=True, check=False,
    )
    if run.returncode:
        raise GuardFailure("V277_GIT_PROOF_UNAVAILABLE_" + args[0])
    return run.stdout


def race_from_source(path: str) -> str | None:
    match = RACE_SOURCE.fullmatch(path)
    if match:
        return match.group(1)
    match = RAW_SOURCE.fullmatch(path)
    if match:
        return f"{match.group(1)}-{match.group(2)}-{match.group(3)}"
    return None


def check_formal(guard: dict) -> None:
    flags = guard.get("guards") if isinstance(guard, dict) else None
    if not isinstance(flags, dict) or any(
        flags.get(k) is not False for k in ("results_seen", "unlock", "scoring")
    ) or flags.get("RESULT_UNLOCK_TOKEN") is not None:
        raise GuardFailure("V277_FORMAL_PRE_RESULT_LOCK_NOT_VERIFIED")
    first = guard.get("formalFirst100") or {}
    if not isinstance(first, dict) or first.get("races") != 0:
        raise GuardFailure("V277_FORMAL_FIRST100_NOT_LOCKED")


def audit(root: Path) -> dict:
    root = Path(root).resolve()
    # Both checkouts must still be PRE_RESULT; no formal unlock or result access.
    try:
        local = json.loads((root / "data/formal_status.json").read_text(encoding="utf8"))
        remote = json.loads(git(root, "show", "origin/main:data/formal_status.json"))
    except (OSError, ValueError, UnicodeError) as exc:
        raise GuardFailure("V277_FORMAL_STATUS_UNREADABLE") from exc
    check_formal(local)
    check_formal(remote)

    ancestor = git(root, "merge-base", "origin/main", "HEAD").strip()
    if not re.fullmatch(r"[0-9a-f]{40,64}", ancestor):
        raise GuardFailure("V277_MERGE_BASE_INVALID")
    changed = set(git(root, "diff", "--name-only", ancestor, "HEAD").splitlines())
    changes = {key for path in changed if (key := race_from_source(path))}
    remote_frozen_paths = set(
        git(root, "ls-tree", "-r", "--name-only", "origin/main", "--", FROZEN_PREFIX).splitlines()
    )
    blocked = [
        key for key in sorted(changes)
        if (FROZEN_PREFIX + key + ".json") in remote_frozen_paths
        or (root / FROZEN_PREFIX / (key + ".json")).is_file()
    ]
    if blocked:
        raise GuardFailure(
            "V277_FROZEN_RACE_SOURCE_MUTATION_BLOCKED_" + ",".join(blocked[:6])
        )
    # The collector is NOT a snapshot creator. If it stages a snapshot by
    # mistake, it must fail, rather than claim provenance from a later run.
    new_snapshots = sorted(p for p in changed if FROZEN.fullmatch(p))
    if new_snapshots:
        raise GuardFailure("V277_COLLECTOR_UNAUTHORIZED_FROZEN_SNAPSHOT_WRITE")
    return {
        "status": "PASS",
        "changed_source_races": len(changes),
        "remote_frozen_snapshots": sum(bool(FROZEN.fullmatch(p)) for p in remote_frozen_paths),
        "formal_results_seen": False,
    }


if __name__ == "__main__":
    try:
        report = audit(Path(sys.argv[1]) if len(sys.argv) > 1 else Path("."))
    except GuardFailure as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1)
    print("V277_COLLECTOR_PUSH_FROZEN_SOURCE_GUARD_PASS " + json.dumps(report, sort_keys=True))
