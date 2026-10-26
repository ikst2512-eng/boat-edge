"""Offline Git-object receipt verifier for a research frozen prediction.

Verifies that a chosen commit introduced a path and that its exact bytes match
the expected SHA256. Commit timestamps are NOT independent wall-clock proof;
a signed external timestamp or a trustworthy GitHub server receipt is required
before admitting a real-race comparison. No Formal Fresh reads/writes.
"""
from __future__ import annotations
import hashlib
import re
import subprocess
from pathlib import Path

HEX40 = re.compile(r"^[0-9a-f]{40}$")
HEX64 = re.compile(r"^[0-9a-f]{64}$")


def _git(repo, *args):
    p = subprocess.run(["git", "-C", str(repo), *args], capture_output=True,
                       check=False, timeout=20)
    if p.returncode:
        raise ValueError("GIT_OBJECT_UNAVAILABLE")
    return p.stdout


def audit_first_add(repo, commit, path, expected_sha256):
    repo = Path(repo)
    if not isinstance(commit, str) or not HEX40.fullmatch(commit):
        raise ValueError("COMMIT_SHA_REQUIRED")
    if not isinstance(expected_sha256, str) or not HEX64.fullmatch(expected_sha256):
        raise ValueError("CONTENT_SHA256_REQUIRED")
    if (not isinstance(path, str) or not path or path.startswith("/")
            or ".." in Path(path).parts or "\\0" in path):
        raise ValueError("SAFE_REPO_PATH_REQUIRED")
    kind = _git(repo, "cat-file", "-t", commit).strip()
    if kind != b"commit":
        raise ValueError("GIT_COMMIT_REQUIRED")
    parents = _git(repo, "rev-list", "--parents", "-n", "1", commit).decode().split()
    if len(parents) != 2:
        raise ValueError("ONE_PARENT_REQUIRED")
    parent = parents[1]
    created = _git(repo, "diff-tree", "--no-commit-id", "--name-only",
                   "--diff-filter=A", "-r", commit, "--", path).decode().splitlines()
    if created != [path]:
        raise ValueError("FIRST_ADD_NOT_PROVEN")
    raw = _git(repo, "show", commit + ":" + path)
    digest = hashlib.sha256(raw).hexdigest()
    if digest != expected_sha256:
        raise ValueError("FROZEN_BYTES_SHA256_MISMATCH")
    return {
        "git_object_first_add_verified": True,
        "git_object_contents_sha256_verified": True,
        "commit": commit,
        "path": path,
        "content_sha256": digest,
        "parent": parent,
        "predeadline_wall_clock_independently_verified": False,
        "unseen_model_independently_verified": False,
        "actual_entry_independently_verified": False,
        "eligible_for_paired_real_race_score": False,
        "formal_fresh_eligible": False,
    }
