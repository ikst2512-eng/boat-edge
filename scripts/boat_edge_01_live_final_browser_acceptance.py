#!/usr/bin/env python3
"""01 delivery gate: trigger actual Pages browser checks on a newly Git-added V229 FINAL.

No result/payout/formal prediction reads. A PASS from browser navigation alone
is NOT certification of saved Top3/5/10.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

JST = timezone(timedelta(hours=9))
KEY = re.compile(r"20\d{6}-\d{2}-\d{2}\Z")
HEX = re.compile(r"[0-9a-f]{64}\Z")
PREFIX = "data/site_autopilot/v229_evidence/"
CERTIFIED = "VERIFIED_SAVED_FINAL_TOP3_TOP5_TOP10_SHA_PARITY"
PAGES = "https://ikst2512-eng.github.io/boat-edge/index.html"


class GateError(ValueError):
    pass


def git(repo: Path, *args: str) -> str:
    done = subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True)
    if done.returncode:
        raise GateError("GIT_PROOF_FAILED_" + args[0])
    return done.stdout.strip()


def utc_stamp(raw):
    try:
        t = datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
        if t.tzinfo is None:
            return None
        return t.astimezone(timezone.utc)
    except (ValueError, TypeError, OverflowError):
        return None


def read(root: Path, name: str):
    p = root / name
    if p.is_symlink() or not p.is_file():
        raise GateError("MISSING_OR_UNSAFE_FILE_" + name)
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (ValueError, UnicodeError, OSError) as exc:
        raise GateError("UNREADABLE_JSON_" + name) from exc


def changed_paths(repo: Path) -> set[str]:
    return set(git(repo, "diff-tree", "--no-commit-id", "--name-only",
                   "-r", "--diff-filter=A", "HEAD").splitlines())


def new_site_final(repo: Path, event: str, expected_sha: str | None = None) -> list[str]:
    if event != "push":
        return []
    head = git(repo, "rev-parse", "HEAD")
    if expected_sha is not None and head != expected_sha:
        raise GateError("CHECKOUT_NOT_TRIGGERING_COMMIT")
    added = changed_paths(repo)
    proofs = sorted(p for p in added if p.startswith(PREFIX))
    if not proofs:
        return []
    formal = read(repo, "data/formal_status.json")
    flags = formal.get("guards") or {}
    if (any(flags.get(k) is not False for k in ("results_seen", "unlock", "scoring"))
            or flags.get("RESULT_UNLOCK_TOKEN") is not None
            or (formal.get("formalFirst100") or {}).get("races") != 0):
        raise GateError("FORMAL_FRESH_NOT_CLOSED")
    committed_at = utc_stamp(git(repo, "log", "-1", "--format=%cI"))
    if committed_at is None:
        raise GateError("FIRST_GIT_COMMIT_TIME_UNAVAILABLE")
    out = []
    for p in proofs:
        key = p[len(PREFIX):-5] if p.endswith(".json") else ""
        if not KEY.fullmatch(key) or p != PREFIX + key + ".json":
            raise GateError("UNSAFE_V229_EVIDENCE_PATH")
        snap_path = "data/site_prediction_snapshots/" + key + ".json"
        audit_path = "data/site_prediction_audit/" + key + ".json"
        if snap_path not in added or audit_path not in added:
            raise GateError("NOT_ATOMIC_FIRST_GIT_ADD_" + key)
        proof = read(repo, p)
        snap = read(repo, snap_path)
        audit = read(repo, audit_path)
        snap_bytes = (repo / snap_path).read_bytes()
        digest = hashlib.sha256(snap_bytes).hexdigest()
        if (proof.get("schema") != "BOAT_EDGE_V229_ATOMIC_PRE_RESULT_SOURCE_EVIDENCE_V1"
                or proof.get("scope") != "SITE_REFERENCE_ONLY_NO_FORMAL_OR_RESULT_ACCESS"
                or proof.get("new_snapshot_created_this_run") is not True
                or proof.get("race_key") != key or snap.get("race_key") != key
                or audit.get("race_key") != key or audit.get("pass") is not True
                or proof.get("snapshot_sha256") != digest
                or audit.get("latest_snapshot_sha256") != digest
                or snap.get("snapshot_window") != "FINAL_15M"
                or snap.get("prediction_kind") != "SITE_REFERENCE_V122"
                or proof.get("snapshot_saved_at") != snap.get("saved_at")
                or any((snap.get("guards") or {}).get(f) is not False
                       for f in ("results_seen", "unlock", "scoring"))
                or proof.get("results_seen") is not False
                or proof.get("formal_fresh_unlock") is not False
                or proof.get("scoring") is not False):
            raise GateError("INVALID_ATOMIC_PRE_RESULT_EVIDENCE_" + key)
        try:
            due = datetime.strptime(key[:8] + str(snap["deadline"]),
                                    "%Y%m%d%H:%M").replace(tzinfo=JST)
        except (KeyError, ValueError, TypeError) as exc:
            raise GateError("INVALID_DEADLINE_" + key) from exc
        first = utc_stamp(snap.get("first_saved_at"))
        saved = utc_stamp(snap.get("saved_at"))
        if not first or not saved or not 2 <= (due-first).total_seconds()/60 <= 10:
            raise GateError("INVALID_FIRST_SAVE_WINDOW_" + key)
        if not first <= saved <= committed_at < due:
            raise GateError("FIRST_GIT_ADD_NOT_BEFORE_DEADLINE_" + key)
        modes = (snap.get("modes") or {})
        hits = ((modes.get("hit") or {}).get("tickets") or [])
        if len(hits) < 10 or len({r.get("combo") for r in hits[:10]}) != 10:
            raise GateError("SAVED_TOP10_NOT_VERIFIED_" + key)
        out.append(key)
    return out


def verify_browser_log(logfile: Path, engine: str) -> dict:
    try:
        source = logfile.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise GateError("PUBLISHED_BROWSER_LOG_MISSING") from exc
    prefix = "BOAT_EDGE_03_REAL_BROWSER_PASS "
    lines = [line.partition(prefix)[2] for line in source.splitlines() if prefix in line]
    if len(lines) != 1:
        raise GateError("PUBLISHED_BROWSER_REPORT_COUNT_INVALID")
    try:
        report = json.loads(lines[0])
    except (ValueError, TypeError) as exc:
        raise GateError("PUBLISHED_BROWSER_REPORT_BAD_JSON") from exc
    live = report.get("live_topk") or {}
    if (report.get("browser") != engine or report.get("target") != PAGES
            or live.get("status") != CERTIFIED
            or live.get("verified_site_final") is not True
            or live.get("displayed_matches_saved_selected_mode") is not True
            or live.get("saved_prediction", {}).get("first_git_commit_verified") is not False
            or not KEY.fullmatch(str(live.get("race") or ""))
            or report.get("physical_iphone_safari_verified") is not False
            or report.get("result_requests_allowed") != 0
            or report.get("formal_fresh_modified") is not False
            or report.get("page_errors")):
        raise GateError("PUBLISHED_SAVED_FINAL_TOPK_NOT_CERTIFIED_" + engine)
    return {"browser": engine, "race": live["race"], "status": CERTIFIED}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="mode", required=True)
    pre = sub.add_parser("preflight")
    pre.add_argument("--repo", type=Path, default=Path("."))
    pre.add_argument("--event", required=True)
    pre.add_argument("--sha")
    pre.add_argument("--github-output", type=Path)
    b = sub.add_parser("browser")
    b.add_argument("--log", type=Path, required=True)
    b.add_argument("--engine", choices=("chromium", "webkit"), required=True)
    opt = parser.parse_args()
    try:
        if opt.mode == "preflight":
            keys = new_site_final(opt.repo, opt.event, opt.sha)
            if opt.github_output:
                with opt.github_output.open("a", encoding="utf-8") as f:
                    f.write("require_saved_final=" + ("true" if keys else "false") + "\n")
            print("V229_PAGES_LIVE_FINAL_REQUIRED " + json.dumps(keys))
        else:
            print("V229_PAGES_LIVE_FINAL_CERTIFIED " + json.dumps(
                verify_browser_log(opt.log, opt.engine), sort_keys=True))
    except GateError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1)
