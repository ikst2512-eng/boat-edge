#!/usr/bin/env python3
"""Stage existing BOAT EDGE public Pages files without reading formal results.

Only browser assets and SITE/PRE_RESULT feeds are included. Formal prediction
cohorts, raw HTML captures, repository internals and source code are excluded.
This script never modifies predictions, Git history, results or publication settings.
"""
from __future__ import annotations

import argparse
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


def copy_public_tree(source: Path, destination: Path) -> int:
    source = Path(source).resolve(strict=True)
    destination = Path(destination).absolute()
    if destination.parent != source or destination.name != "_pages_site":
        raise ValueError("Output must be the repository's _pages_site directory")
    if destination.is_symlink():
        raise ValueError("Refusing symlink destination")
    for item in REQUIRED:
        path = source / item
        if not path.is_file() or path.is_symlink():
            raise ValueError("Missing or unsafe public asset: " + item)
    selected = sorted(source.glob("*.html")) + [source / ".nojekyll", source / "assets"]
    data = source / "data"
    for item in sorted(data.iterdir()):
        if item.is_file() and item.name in PUBLIC_DATA_FILES:
            selected.append(item)
        elif item.is_dir() and (item.name.startswith("site_") or item.name == "races"):
            selected.append(item)
    for item in selected:
        if item.is_symlink() or any(p.is_symlink() for p in item.rglob("*")) if item.is_dir() else item.is_symlink():
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
    return count


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", default=".")
    parser.add_argument("--dest", default="_pages_site")
    args = parser.parse_args()
    total = copy_public_tree(Path(args.repo), Path(args.repo) / args.dest)
    print("PAGES_STAGED_PUBLIC_FILES", total)
    return 0


if __name__ == "__main__":
    sys.exit(main())
