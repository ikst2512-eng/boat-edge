"""Pre-scoring, fail-closed local Git proof checker; NEVER reads race outcomes.

A PASS establishes local Git-object consistency only. Git commit timestamps are
self-declared, and cannot independently attest publication before race deadline.
"""
import argparse
import hashlib
import json
import re
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

SHA256 = re.compile(r"^[0-9a-f]{64}$")
GIT_SHA = re.compile(r"^[0-9a-f]{40}$")
JST = timedelta(hours=9)


def git(root, *args):
    p = subprocess.run(["git", *args], cwd=root, stdout=subprocess.PIPE,
                       stderr=subprocess.PIPE, check=False)
    if p.returncode:
        raise ValueError("GIT_PROOF_UNAVAILABLE")
    return p.stdout


def timestamp(s):
    t = datetime.fromisoformat(s)
    if t.utcoffset() != JST:
        raise ValueError("JST_TIMESTAMP_REQUIRED")
    return t


def verify(root, manifest):
    """Check a supplied *pre-outcome* paired manifest, never discover results."""
    if not isinstance(manifest, dict) or manifest.get("scope") != "RESEARCH_ONLY_PRE_OUTCOME_PAIR":
        raise ValueError("RESEARCH_SCOPE_REQUIRED")
    race = manifest.get("race_key")
    if not isinstance(race, str) or not re.fullmatch(r"20[0-9]{6}-(?:0[1-9]|1[0-9]|2[0-4])-(?:0[1-9]|1[0-2])", race):
        raise ValueError("BAD_RACE_KEY")
    deadline = timestamp(manifest["deadline_jst"])
    if deadline.strftime("%Y%m%d") != race[:8]:
        raise ValueError("DEADLINE_RACE_MISMATCH")
    inputs = []
    for side in ("baseline", "candidate"):
        item = manifest.get(side)
        if not isinstance(item, dict):
            raise ValueError("MISSING_SIDE_" + side)
        for field in ("input", "prediction", "model"):
            artifact = item.get(field)
            if not isinstance(artifact, dict):
                raise ValueError("MISSING_ARTIFACT_" + side + "_" + field)
            path, digest, commit = (artifact.get(x) for x in ("path", "sha256", "first_commit"))
            if not isinstance(path, str) or not path or Path(path).is_absolute() or ".." in Path(path).parts or "\\" in path:
                raise ValueError("INVALID_RELATIVE_PATH")
            if not isinstance(digest, str) or not SHA256.fullmatch(digest):
                raise ValueError("INVALID_SHA256")
            if not isinstance(commit, str) or not GIT_SHA.fullmatch(commit):
                raise ValueError("INVALID_GIT_SHA")
            # Read bytes from immutable Git tree, not mutable working tree.
            raw = git(root, "show", commit + ":" + path)
            if hashlib.sha256(raw).hexdigest() != digest:
                raise ValueError("GIT_TREE_BYTES_SHA_MISMATCH")
            first = git(root, "log", "--follow", "--diff-filter=A",
                        "--format=%H", commit, "--", path).decode().splitlines()
            if len(first) != 1 or first[0] != commit:
                raise ValueError("NOT_FIRST_GIT_ADD")
            committed = timestamp(git(root, "show", "-s", "--format=%cI", commit).decode().strip())
            if committed >= deadline:
                raise ValueError("NOT_PREDEADLINE_GIT_TIME")
            if field == "prediction":
                # A self-declared freeze time cannot substitute for the Git check.
                saved = timestamp(item["prediction_saved_at_jst"])
                if saved >= deadline or saved > committed:
                    raise ValueError("INVALID_PREDICTION_FREEZE_TIME")
            if field == "input":
                inputs.append(digest)
    if inputs[0] != inputs[1]:
        raise ValueError("DIFFERENT_INPUT_BYTES")
    return {
        "race_key": race,
        "local_git_object_consistency": "PASS",
        "input_sha256": inputs[0],
        "independent_publication_time_proven": False,
        "model_outcome_blindness_proven": False,
        "comparable_for_real_race_scoring": False,
        "formal_fresh_read": False,
        "decision": "HOLD_INDEPENDENT_ATTESTATION_AND_MODEL_BLINDNESS_REQUIRED",
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--root", type=Path, default=Path("."))
    p.add_argument("--manifest", type=Path, required=True)
    args = p.parse_args()
    data = json.loads(args.manifest.read_text(encoding="utf-8"))
    print(json.dumps(verify(args.root.resolve(), data), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
