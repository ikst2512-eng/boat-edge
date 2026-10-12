#!/usr/bin/env python3
"""V277 offline Git concurrency regression: no network, no race result reads."""
from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.boat_edge_v277_snapshot_push_guard import (
    GuardFailure, audit, race_from_source,
)

KEY = "20261013-19-08"
NEXT = "20261013-19-09"
RACE = f"data/races/{KEY}.json"
RAW = "data/raw/20261013/19_08_beforeinfo.html"
SNAP = f"data/site_prediction_snapshots/{KEY}.json"
FORMAL = "data/formal_status.json"


def cmd(repo: Path, *args: str) -> str:
    proc = subprocess.run(
        ["git", *args], cwd=repo, capture_output=True, text=True, check=False
    )
    assert proc.returncode == 0, (args, proc.stdout, proc.stderr)
    return proc.stdout.strip()


def put(repo: Path, path: str, content: str) -> None:
    p = repo / path
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf8")


def commit(repo: Path, message: str) -> None:
    cmd(repo, "add", "-A")
    cmd(repo, "commit", "-m", message)


def check_reject(repo: Path, tag: str) -> None:
    try:
        audit(repo)
    except GuardFailure as exc:
        assert tag in str(exc), (tag, str(exc))
    else:
        raise AssertionError("V277_FAIL_OPEN_" + tag)


assert race_from_source(RACE) == KEY
assert race_from_source(RAW) == KEY
assert race_from_source("data/raw/20261013/19_08_racelist.html") == KEY
assert race_from_source("data/site_odds/index.json") is None
assert race_from_source("data/races/../../escape.json") is None

with tempfile.TemporaryDirectory() as td:
    base = Path(td)
    upstream = base / "remote.git"
    owner = base / "collector"
    cmd(base, "init", "--bare", "-b", "main", str(upstream))
    cmd(base, "clone", str(upstream), str(owner))
    cmd(owner, "config", "user.email", "ci@example.test")
    cmd(owner, "config", "user.name", "CI")

    lock = {
        "guards": {
            "results_seen": False, "unlock": False, "scoring": False,
            "RESULT_UNLOCK_TOKEN": None,
        },
        "formalFirst100": {"races": 0},
    }
    put(owner, FORMAL, json.dumps(lock))
    put(owner, RACE, '{"race_key": "20261013-19-08", "source": "first"}\n')
    put(owner, RAW, "<html>source-1</html>\n")
    commit(owner, "base pre-result")
    cmd(owner, "push", "-u", "origin", "main")
    assert audit(owner)["status"] == "PASS"

    # Collector begins from initial data. Its change is valid UNTIL V235
    # independently freezes the same race and commits that snapshot upstream.
    put(owner, RACE, '{"race_key": "20261013-19-08", "source": "second"}\n')
    commit(owner, "collector edited race after checkout")
    assert audit(owner)["changed_source_races"] == 1

    other = base / "v235"
    cmd(base, "clone", str(upstream), str(other))
    cmd(other, "config", "user.email", "ci@example.test")
    cmd(other, "config", "user.name", "CI")
    put(other, SNAP, "{frozen content is not read by the V277 guard}")
    commit(other, "V235 freezes previously published pre-result race")
    cmd(other, "push", "origin", "main")
    cmd(owner, "fetch", "--no-tags", "origin", "main")
    check_reject(owner, "V277_FROZEN_RACE_SOURCE_MUTATION_BLOCKED")

    # Source changes to another, never frozen race are still eligible.
    cmd(owner, "reset", "--hard", "origin/main")
    put(owner, f"data/races/{NEXT}.json", '{"race_key":"20261013-19-09"}\n')
    commit(owner, "a still unfrozen next race")
    assert audit(owner)["changed_source_races"] == 1

    # Raw HTML from a frozen race is also immutable, not just the parsed JSON.
    cmd(owner, "reset", "--hard", "origin/main")
    put(owner, RAW, "<html>late mutation</html>\n")
    commit(owner, "late beforeinfo raw overwrite")
    check_reject(owner, "V277_FROZEN_RACE_SOURCE_MUTATION_BLOCKED")

    # Reject accidental snapshot creation by a generic collector.
    cmd(owner, "reset", "--hard", "origin/main")
    put(owner, f"data/site_prediction_snapshots/{NEXT}.json", "{}")
    commit(owner, "collector must not create a frozen snapshot")
    check_reject(owner, "V277_COLLECTOR_UNAUTHORIZED_FROZEN_SNAPSHOT_WRITE")

    # A mutated formal lock is never permission to publish.
    cmd(owner, "reset", "--hard", "origin/main")
    lock["guards"]["results_seen"] = True
    put(owner, FORMAL, json.dumps(lock))
    commit(owner, "unsafe formal status")
    check_reject(owner, "V277_FORMAL_PRE_RESULT_LOCK_NOT_VERIFIED")

wf = Path(".github/workflows/auto-update.yml").read_text(encoding="utf8")
assert "git fetch --no-tags origin main\n            PYTHONDONTWRITEBYTECODE=1 python3 scripts/boat_edge_v277_snapshot_push_guard.py" in wf
assert wf.index("scripts/boat_edge_v277_snapshot_push_guard.py") < wf.index("if git push origin HEAD:main")
print("V277_CONCURRENT_POST_FREEZE_SOURCE_PUSH_FAIL_CLOSED_PASS")
