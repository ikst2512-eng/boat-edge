#!/usr/bin/env python3
"""Conservatively remove ONLY in-flight collector changes for newly Git-frozen races.

The unchanged V277 audit still has final authority. This helper never reads
snapshot contents, results, payout data or model outputs. It is ONLY invoked
after V277 detects a concurrently frozen race in a PRE_RESULT collector commit.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import re
import subprocess

from scripts.boat_edge_v277_snapshot_push_guard import (
    GuardFailure, check_formal, git, race_from_source, SOURCE_LOCK_PREFIXES,
)

JST = timezone(timedelta(hours=9))
COLLECTOR = "自動更新: PRE_RESULT "
SCRATCH = re.compile(r"data/site_scratches_v182/(20\d{6}-\d{2}-\d{2})\.json\Z")
PREVIEW = re.compile(r"data/site_early_previews/(20\d{6}-\d{2}-\d{2})\.json\Z")


def checked_run(root: Path, *args: str) -> str:
    proc = subprocess.run(["git", *args], cwd=root,
                          capture_output=True, text=True, check=False)
    if proc.returncode:
        raise GuardFailure("V01_FROZEN_FILTER_GIT_REFUSED_" + args[0]
                           + "_" + proc.stderr[:180])
    return proc.stdout


def read_remote_formal(root: Path) -> None:
    try:
        local = json.loads((root / "data/formal_status.json").read_text(encoding="utf8"))
        remote = json.loads(git(root, "show", "origin/main:data/formal_status.json"))
    except (OSError, ValueError, UnicodeError) as ex:
        raise GuardFailure("V01_FORMAL_STATUS_MISSING") from ex
    check_formal(local)
    check_formal(remote)


def changed_files(root: Path) -> list[str]:
    base = git(root, "merge-base", "origin/main", "HEAD").strip()
    if not re.fullmatch(r"[0-9a-f]{40,64}", base):
        raise GuardFailure("V01_UNPROVEN_BASE")
    return [p for p in git(root, "diff", "--name-only", base, "HEAD").splitlines() if p]


def frozen_keys(root: Path) -> set[str]:
    keys: set[str] = set()
    for prefix in SOURCE_LOCK_PREFIXES:
        for path in git(root, "ls-tree", "-r", "--name-only", "origin/main", "--", prefix).splitlines():
            if path.startswith(prefix) and path.endswith(".json"):
                key = path[len(prefix):-5]
                if re.fullmatch(r"20\d{6}-\d{2}-\d{2}", key):
                    keys.add(key)
    return keys


def origin_has(root: Path, file: str) -> bool:
    proc = subprocess.run(
        ["git", "cat-file", "-e", "origin/main:" + file], cwd=root,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
    return proc.returncode == 0


def filter_newly_frozen(root: Path) -> dict:
    root = Path(root).resolve()
    read_remote_formal(root)
    if git(root, "status", "--porcelain", "--untracked-files=no").strip():
        raise GuardFailure("V01_COLLECTOR_WORKTREE_NOT_CLEAN")
    title = git(root, "log", "-1", "--format=%s", "HEAD").strip()
    if not title.startswith(COLLECTOR):
        raise GuardFailure("V01_NOT_A_ROLLING_PRE_RESULT_COLLECTOR_COMMIT")
    diff = changed_files(root)
    illegal = [p for p in diff if p.startswith((
        "data/site_prediction_snapshots/", "data/site_autopilot/v232_cohort/",
        "data/formal_predictions/", "data/formal/", "data/site_results/"
    ))]
    if illegal:
        raise GuardFailure("V01_COLLECTOR_HAS_NON_SOURCE_OR_FROZEN_PATH")
    frozen = frozen_keys(root)
    changed_sources = {key for path in diff if (key := race_from_source(path))}
    keys = sorted(changed_sources & frozen)
    if not keys:
        raise GuardFailure("V01_NO_NEWLY_REMOTE_FROZEN_SOURCE_TO_FILTER")
    now = datetime.now(JST)
    # The collector must not publish source bytes after a deadline merely
    # because an earlier run fetched them before the race's deadline.
    for key in sorted(changed_sources - set(keys)):
        p = root / "data/races" / (key + ".json")
        try:
            doc = json.loads(p.read_text(encoding="utf8"))
            meta = doc["meta"]
            due = datetime.strptime(key[:8] + meta["deadline"], "%Y%m%d%H:%M").replace(tzinfo=JST)
        except (OSError, UnicodeError, ValueError, TypeError, KeyError) as ex:
            raise GuardFailure("V01_REMAINING_SOURCE_DEADLINE_UNVERIFIED_" + key) from ex
        if now >= due:
            raise GuardFailure("V01_REMAINING_SOURCE_DEADLINE_PASSED_" + key)

    dropped: list[str] = []
    for file in diff:
        source = race_from_source(file)
        scratch = SCRATCH.fullmatch(file)
        preview = PREVIEW.fullmatch(file)
        key = source or (scratch.group(1) if scratch else
                         preview.group(1) if preview else None)
        if key not in keys:
            continue
        # Origin is authoritative: a remote snapshot or V232 cohort has already
        # immutably locked its source, even if source bytes locally look fresher.
        if origin_has(root, file):
            checked_run(root, "restore", "--source=origin/main", "--staged", "--worktree", "--", file)
        else:
            checked_run(root, "rm", "-f", "--ignore-unmatch", "--", file)
        dropped.append(file)

    if not dropped:
        raise GuardFailure("V01_FROZEN_SOURCE_NOT_DROPPED")

    # Race chooser index cannot report locally refreshed, discarded race data.
    today = root / "data/today.json"
    if today.is_file() and "data/today.json" in diff:
        try:
            local_doc = json.loads(today.read_text(encoding="utf8"))
            remote_doc = json.loads(git(root, "show", "origin/main:data/today.json"))
            if (local_doc.get("date") != remote_doc.get("date")
                    or local_doc.get("results_seen") is not False
                    or remote_doc.get("results_seen") is not False):
                raise GuardFailure("V01_TODAY_INDEX_RACE_STATE_NOT_PROVABLE")
            by_key = {r["race_key"]: r for v in remote_doc["venues"]
                      for r in v["races"] if isinstance(r, dict) and "race_key" in r}
            seen = set()
            for venue in local_doc["venues"]:
                for index, item in enumerate(venue["races"]):
                    key = item.get("race_key")
                    if key in keys:
                        if key not in by_key:
                            raise GuardFailure("V01_FROZEN_RACE_MISSING_IN_REMOTE_CATALOG")
                        venue["races"][index] = by_key[key]
                        seen.add(key)
            if seen != set(keys):
                raise GuardFailure("V01_FROZEN_RACE_NOT_PRESENT_IN_LOCAL_CATALOG")
        except (OSError, UnicodeError, ValueError, TypeError, KeyError) as ex:
            raise GuardFailure("V01_CATALOG_PARSE_FAILED") from ex
        today.write_text(json.dumps(local_doc, ensure_ascii=False, indent=2), encoding="utf8")
        checked_run(root, "add", "--", "data/today.json")

    # Material diagnostic: current health counts describe fetched rather
    # than accepted source, so clearly mark any intentionally discarded races.
    hp = root / "data/health.json"
    if hp.is_file() and "data/health.json" in diff:
        try:
            health = json.loads(hp.read_text(encoding="utf8"))
        except (OSError, UnicodeError, ValueError) as ex:
            raise GuardFailure("V01_HEALTH_UNVERIFIED") from ex
        if any(health.get(flag) is not False for flag in ("results_seen", "unlock", "scoring")):
            raise GuardFailure("V01_HEALTH_RESULT_UNSAFE")
        health["collector_source_published_exclusions"] = keys
        health["collector_source_stats_are_fetch_only"] = True
        hp.write_text(json.dumps(health, ensure_ascii=False, indent=2), encoding="utf8")
        checked_run(root, "add", "--", "data/health.json")

    # One local commit only. Existing V277 audit is then repeated against the
    # newly amended exact Git bytes BEFORE any push. No --force is used.
    checked_run(root, "commit", "--amend", "--no-edit", "--allow-empty")
    return {"pruned_frozen_races": keys, "dropped_paths": dropped,
            "results_seen": False, "remote_evidence_preserved": True}
