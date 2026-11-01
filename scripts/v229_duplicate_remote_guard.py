#!/usr/bin/env python3
"""Only acknowledge a V229 rejected push if every committed file is byte-identical on origin/main.

Never rewrite a first-writer snapshot or mark a different payload as saved.
Called after the failed rebase is aborted, while HEAD is our original candidate commit.
"""
import subprocess
import sys

def git(*args):
    return subprocess.run(["git", *args], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                          check=False).stdout

def duplicate_on_remote():
    names = git("diff-tree", "--no-commit-id", "--name-only", "-r", "HEAD").decode().splitlines()
    if not names:
        return False
    for name in names:
        if not (name.startswith(("data/site_prediction_snapshots/", "data/site_prediction_audit/",
                                 "data/site_autopilot/v229_evidence/"))):
            return False
        local = subprocess.run(["git", "rev-parse", f"HEAD:{name}"], capture_output=True)
        remote = subprocess.run(["git", "rev-parse", f"origin/main:{name}"], capture_output=True)
        if local.returncode != 0 or remote.returncode != 0 or local.stdout != remote.stdout:
            return False
    return True

if __name__ == "__main__":
    sys.exit(0 if duplicate_on_remote() else 1)
