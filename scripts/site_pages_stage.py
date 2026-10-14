#!/usr/bin/env python3
"""Stage existing BOAT EDGE public Pages files without reading formal results.

Only browser assets and SITE/PRE_RESULT feeds are included. Formal prediction
cohorts, raw HTML captures, repository internals and source code are excluded.
This script never modifies predictions, Git history, results or publication settings.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
import shutil
import sys

PUBLIC_DATA_FILES = frozenset({
    "formal_status.json",
    "health.json",
    "model_status.json",
    "site_current_state.json",
    "site_health.json",
    "site_latest_bridge_contract.json",
    "site_latest_v178_parity_contract.json",
    "site_prediction_policy.json",
    "site_todo_evidence.json",
    "site_ui_display_requirements.json",
    "today.json",
})
REQUIRED = (
    "index.html",
    "autopilot.html",
    ".nojekyll",
    "assets/boat_edge_v108.js",
    "data/today.json",
    "data/formal_status.json",
)


def copy_public_tree(source: Path, destination: Path, source_commit_sha: str | None = None) -> int:
    source = Path(source).resolve(strict=True)
    destination = Path(destination).absolute()
    if destination.parent != source or destination.name != "_pages_site":
        raise ValueError("Output must be the repository's _pages_site directory")
    if source_commit_sha is not None and not re.fullmatch(r"[0-9a-f]{40}", source_commit_sha):
        raise ValueError("A published source commit must be exactly 40 lowercase hex characters")
    if destination.is_symlink():
        raise ValueError("Refusing symlink destination")
    for item in REQUIRED:
        path = source / item
        if not path.is_file() or path.is_symlink():
            raise ValueError("Missing or unsafe public asset: " + item)
    # Site results are allowed only while the independent FORMAL Fresh gate
    # remains closed. Never open formal predictions, payouts, or results.
    try:
        formal = json.loads((source / "data/formal_status.json").read_text(encoding="utf-8"))
        guards = formal["guards"]
        cohort = formal["formalFirst100"]
        if (any(guards.get(key) is not False for key in ("results_seen", "unlock", "scoring"))
                or guards.get("RESULT_UNLOCK_TOKEN") is not None
                or type(cohort.get("races")) is not int or cohort["races"] != 0):
            raise ValueError("Formal Fresh lock not independently closed")
    except (OSError, UnicodeError, KeyError, TypeError, json.JSONDecodeError) as exc:
        raise ValueError("Formal Fresh lock unavailable") from exc
    selected = sorted(source.glob("*.html")) + [source / ".nojekyll", source / "assets"]
    data = source / "data"
    for item in sorted(data.iterdir()):
        if item.is_file() and item.name in PUBLIC_DATA_FILES:
            selected.append(item)
        elif item.is_dir() and (item.name.startswith("site_") or item.name == "races"):
            selected.append(item)
    for item in selected:
        if item.is_symlink() or (item.is_dir() and any(p.is_symlink() for p in item.rglob("*"))):
            raise ValueError("Symlink in published asset: " + str(item.relative_to(source)))
    if destination.exists():
        if not destination.is_dir():
            raise ValueError("Unsafe output path")
        shutil.rmtree(destination)
    destination.mkdir()
    count = 0
    for item in selected:
        target = destination / item.relative_to(source)
        if item.is_dir():
            shutil.copytree(item, target, symlinks=False)
            count += sum(p.is_file() for p in target.rglob("*"))
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(item, target)
            count += 1
    if not all((destination / rel).is_file() for rel in REQUIRED):
        raise AssertionError("Staged site incomplete")
    if (destination / "data/raw").exists() or (destination / "data/formal_predictions").exists():
        raise AssertionError("Restricted data entered the Pages artifact")
    if source_commit_sha is not None:
        # The manifest is generated inside the deploy artifact, never in main.
        # These digests describe published bytes, not a prediction freeze or
        # proof that a particular race was committed before its deadline.
        attest_paths = ("index.html", "assets/boat_edge_v108.js",
                        "data/today.json", "data/formal_status.json")
        manifest = {
            "schema": "BOAT_EDGE_PAGES_SOURCE_MANIFEST_V1",
            "source_commit_sha": source_commit_sha,
            "published_file_sha256": {
                p: hashlib.sha256((destination / p).read_bytes()).hexdigest()
                for p in attest_paths
            },
        }
        (destination / "data/site_release_manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
            encoding="utf-8",
        )
        count += 1
    return count


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", default=".")
    parser.add_argument("--dest", default="_pages_site")
    parser.add_argument("--source-sha", default=None)
    args = parser.parse_args()
    total = copy_public_tree(Path(args.repo), Path(args.repo) / args.dest, args.source_sha)
    print("PAGES_STAGED_PUBLIC_FILES", total)
    return 0


if __name__ == "__main__":
    sys.exit(main())
