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


def first_git_add_proof(root, path):
    """Read Git's first-add timestamp AND original bytes, not current HEAD bytes.

    A later commit could replace the saved snapshot and update its audit/receipt
    consistently. SHA parity among those mutable HEAD files does not establish
    that the SAME bytes existed at the first predeadline Git addition.
    """
    relative = path.relative_to(root).as_posix()
    history = subprocess.run(
        ["git", "log", "--diff-filter=A", "--format=%H%x09%cI", "--", relative],
        cwd=root, capture_output=True, text=True, check=False,
    )
    if history.returncode:
        return None
    rows = [line.split("\t") for line in history.stdout.splitlines()]
    if not rows or any(
            len(row) != 2 or not re.fullmatch(r"[0-9a-f]{40}", row[0])
            or instant(row[1]) is None for row in rows):
        return None
    # Git log emits newest first; oldest first-add wins even if a later
    # commit has an incorrectly set author/committer clock.
    original_commit, timestamp = rows[-1]
    original = subprocess.run(
        ["git", "show", original_commit + ":" + relative],
        cwd=root, capture_output=True, check=False,
    )
    if original.returncode:
        return None
    return instant(timestamp), hashlib.sha256(original.stdout).hexdigest(), original_commit


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
    # Git %cI is SECOND precision whereas the frozen saved_at is often
    # microsecond precision. A first Git commit at 14:29:45 and a snapshot
    # saved at 14:29:45.646 are in the SAME recorded Git second, not evidence
    # that the commit preceded the snapshot. Compare at Git's precision,
    # while still rejecting a commit from a whole second earlier and any
    # commit at or after the exact deadline.
    git_precision_saved_at = at.replace(microsecond=0)
    if not (2 * 60 <= (due-first).total_seconds() <= 10 * 60
            and 2 * 60 <= (due-now).total_seconds() <= 15 * 60
            and first <= at and git_precision_saved_at <= first_add <= now < due):
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
    # V125 can add an explicitly empty, PRE_RESULT-only sentinel before the
    # race. Any populated, malformed or additional settlement field is unsafe.
    if "settlement" in audit:
        settlement = audit["settlement"]
        if (not isinstance(settlement, dict)
                or set(settlement) != {
                    "available", "winning_combo", "hit_any", "mode_hits", "payout"
                }
                or settlement.get("available") is not False
                or settlement.get("winning_combo") is not None
                or settlement.get("hit_any") is not None
                or settlement.get("mode_hits") != {}
                or settlement.get("payout") is not None):
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
        proof = first_git_add_proof(root, snapshot_path)
        if proof is None:
            continue
        commit_at, original_digest, original_commit = proof
        current_digest = hashlib.sha256(raw).hexdigest()
        # The same race's first Git ADD must contain the exact bytes
        # currently displayed. Self-consistent rewritten audits cannot pass.
        if original_digest != current_digest:
            continue
        if valid(snapshot, audit, receipt, raw, key, now, commit_at):
            eligible.append({"race_key": key, "deadline": snapshot["deadline"],
                             "first_git_add_utc": commit_at.isoformat(),
                             "first_git_commit_sha": original_commit,
                             "snapshot_sha256": current_digest})
    return eligible


def selected_live_race(checked):
    """Choose ONE proven race with the most live time left for both browsers.

    Do not re-rank predictions; only choose the read-only E2E subject. Both
    engines MUST receive this same predeclared race, even if racing progresses.
    """
    if not checked:
        return None
    return max(checked, key=lambda item: (
        item["race_key"][:8] + item["deadline"].replace(":", ""),
        item["race_key"],
    ))["race_key"]


if __name__ == "__main__":
    now = datetime.now(timezone.utc)
    checked = candidates(Path("."), now)
    selected = selected_live_race(checked)
    output = os.environ.get("GITHUB_OUTPUT")
    if output:
        with open(output, "a", encoding="utf-8") as f:
            f.write("live_candidate=" + ("true" if selected else "false") + "\n")
            f.write("selected_race=" + (selected or "") + "\n")
            # Same immutable SHA identity must be proven again by BOTH public
            # browsers. A different saved race must never borrow this Git
            # first-add proof, even if its own SITE audit superficially passes.
            f.write("first_add_proofs=" + ",".join(
                item["race_key"] + ":" + item["snapshot_sha256"]
                for item in checked
            ) + "\n")
    print("V01_LIVE_BROWSER_ACTUAL_PREDEADLINE_GATE " +
          json.dumps({"eligible_count": len(checked),
                      "selected_race": selected,
                      "eligible": checked[:4],
                      "browser_pass_claimed": False,
                      "formal_fresh_untouched": True},
                     ensure_ascii=False, sort_keys=True))
