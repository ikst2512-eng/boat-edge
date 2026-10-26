#!/usr/bin/env python3
"""Prospective model-source identity sidecar, research only.

Run before deadline; sidecar is NOT an eligible prediction until independently
committed to Git before deadline. Never backfill historical cohorts.
"""
import argparse
import ast
import datetime as dt
import hashlib
import json
import re
import subprocess
from pathlib import Path

KEY = re.compile(r"^20[0-9]{6}-[0-9]{2}-[0-9]{2}$")
HEX40 = re.compile(r"^[0-9a-f]{40}$")


def git(root, *args):
    p = subprocess.run(["git", *args], cwd=root, capture_output=True)
    if p.returncode:
        raise ValueError("GIT_PROVENANCE_COMMAND_FAILED")
    return p.stdout


def local_import_paths(root, source):
    """Resolve only direct local Python imports; unresolved imports remain blockers."""
    tree = ast.parse(source.read_text(encoding="utf-8"))
    found = set()
    for node in ast.walk(tree):
        names = []
        if isinstance(node, ast.Import):
            names = [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            names = [node.module or ""]
            if node.level:
                raise ValueError("RELATIVE_IMPORT_REQUIRES_MANUAL_CLOSURE")
        for name in names:
            if not name:
                continue
            stem = name.split(".")[0]
            candidate = source.parent / (stem + ".py")
            candidate2 = root / "scripts" / (stem + ".py")
            if candidate.is_file():
                found.add(candidate.relative_to(root).as_posix())
            elif candidate2.is_file():
                found.add(candidate2.relative_to(root).as_posix())
    return found


def create(root, race_key, model_path, deadline_jst, now=None, dependency_paths=()):
    root = Path(root).resolve()
    if not KEY.fullmatch(race_key):
        raise ValueError("INVALID_RACE_KEY")
    deadline = dt.datetime.fromisoformat(deadline_jst.replace("Z", "+00:00"))
    now = now or dt.datetime.now(dt.timezone.utc)
    if deadline.tzinfo is None or now.tzinfo is None or now >= deadline:
        raise ValueError("LIVE_PREDEADLINE_ONLY")
    rel = Path(model_path)
    if rel.is_absolute() or ".." in rel.parts or not rel.parts:
        raise ValueError("UNSAFE_MODEL_PATH")
    source = root / rel
    if source.is_symlink() or not source.is_file():
        raise ValueError("MODEL_SOURCE_MISSING_OR_SYMLINK")
    sha = git(root, "rev-parse", "HEAD").decode().strip()
    if not HEX40.fullmatch(sha):
        raise ValueError("INVALID_GIT_SHA")
    tracked = git(root, "ls-files", "--error-unmatch", "--", rel.as_posix())
    if not tracked:
        raise ValueError("MODEL_NOT_TRACKED")
    original = git(root, "show", f"{sha}:{rel.as_posix()}")
    local = source.read_bytes()
    if local != original:
        raise ValueError("MODEL_DIFFERS_FROM_HEAD")
    dependencies = {}
    detected_imports = local_import_paths(root, source)
    requested = set(dependency_paths)
    if not detected_imports.issubset(requested):
        raise ValueError("DIRECT_LOCAL_DEPENDENCIES_NOT_DECLARED")
    for item in dependency_paths:
        dependency = Path(item)
        if (dependency.is_absolute() or ".." in dependency.parts or not dependency.parts
                or dependency.as_posix() == rel.as_posix()
                or dependency.as_posix() in dependencies):
            raise ValueError("INVALID_DEPENDENCY_PATH")
        dep_file = root / dependency
        if dep_file.is_symlink() or not dep_file.is_file():
            raise ValueError("DEPENDENCY_MISSING_OR_SYMLINK")
        if not git(root, "ls-files", "--error-unmatch", "--", dependency.as_posix()):
            raise ValueError("DEPENDENCY_NOT_TRACKED")
        committed = git(root, "show", f"{sha}:{dependency.as_posix()}")
        if dep_file.read_bytes() != committed:
            raise ValueError("DEPENDENCY_DIFFERS_FROM_HEAD")
        dependencies[dependency.as_posix()] = hashlib.sha256(committed).hexdigest()
    return {
        "schema": "BOAT_EDGE_PROSPECTIVE_MODEL_IDENTITY_V1",
        "scope": "SITE_RESEARCH_ONLY_NOT_FORMAL_FRESH",
        "race_key": race_key,
        "deadline_jst": deadline.isoformat(),
        "recorded_at": now.isoformat(),
        "model_path": rel.as_posix(),
        "model_source_scope": "SINGLE_FILE_ONLY_DEPENDENCIES_NOT_ATTESTED",
        "model_git_sha": sha,
        "model_source_sha256": hashlib.sha256(original).hexdigest(),
        "declared_dependency_sha256": dict(sorted(dependencies.items())),
        "direct_local_imports_checked": sorted(detected_imports),
        "dependency_set_complete_independently_verified": False,
        "git_first_add_before_deadline_independently_verified": False,
        "prediction_eligibility_granted": False,
        "accuracy_improvement_proven": False,
        "formal_fresh_unlocked": False,
    }


def save_once(root, record):
    root = Path(root).resolve()
    dest = root / "data/site_research_model_receipts" / (record["race_key"] + ".json")
    dest.parent.mkdir(parents=True, exist_ok=True)
    payload = (json.dumps(record, sort_keys=True, ensure_ascii=False, indent=2) + "\n").encode()
    with dest.open("xb") as f:
        f.write(payload)
    return dest


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--root", type=Path, default=Path("."))
    p.add_argument("--race-key", required=True)
    p.add_argument("--model-path", required=True)
    p.add_argument("--deadline-jst", required=True)
    p.add_argument("--dependency-path", action="append", default=[])
    args = p.parse_args()
    record = create(args.root, args.race_key, args.model_path, args.deadline_jst, dependency_paths=args.dependency_path)
    print(save_once(args.root, record))
