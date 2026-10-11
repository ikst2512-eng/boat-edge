#!/usr/bin/env python3
"""Guard unattended UI-only edits; never touch Fresh/prediction/result data."""
from __future__ import annotations
import argparse
from pathlib import Path
import re
import subprocess
import sys

QUEUE = "BOAT_EDGE_AUTODEV_TASKS.md"
TASK = re.compile(r"^- \[ \] (A\d{2}) \| (.+)$", re.MULTILINE)
ALLOWED_PAGES = {
    "index.html", "autopilot.html", "health.html", "hit-rate.html",
    "accuracy.html", "ai-simulation.html", "cohort.html",
    "second-tail.html", "tail-diagnostics.html",
}
ALLOWED_ASSET = re.compile(r"^assets/boat_edge_[a-zA-Z0-9_]+\.(?:js|css)$")
PROHIBITED_ADDITIONS = (
    "RESULT_UNLOCK_TOKEN", "data/formal_", "data/site_results",
    "raceresult", "document.write(", "eval(", "<iframe",
)
MAX_UI_FILES = 4
MAX_CHANGED_LINES = 300


def git(*args: str) -> str:
    return subprocess.check_output(("git", *args), text=True, encoding="utf-8")


def first_pending(source: str) -> tuple[str, str] | None:
    match = TASK.search(source)
    return (match.group(1), match.group(2)) if match else None


def completed_once(old: str, new: str) -> bool:
    task = first_pending(old)
    if task is None:
        return False
    needle = f"- [ ] {task[0]} | {task[1]}"
    return new == old.replace(needle, needle.replace("[ ]", "[x]"), 1)


def permitted_ui(path: str) -> bool:
    return path in ALLOWED_PAGES or bool(ALLOWED_ASSET.fullmatch(path))


def verify() -> tuple[int, str]:
    old_queue = git("show", f"HEAD:{QUEUE}")
    new_queue = Path(QUEUE).read_text(encoding="utf-8")
    if not completed_once(old_queue, new_queue):
        return 2, "FAIL: exactly the first pending task must be checked off; no other queue edits"
    statuses = git("status", "--porcelain", "--untracked-files=all").splitlines()
    if not statuses:
        return 2, "FAIL: no changes"
    paths = []
    for status in statuses:
        if not status.startswith(" M "):
            return 2, f"FAIL: untracked, staged, renamed or deleted file: {status[:120]}"
        path = status[3:]
        if "\\x00" in path or path.startswith('"') or ".." in Path(path).parts:
            return 2, "FAIL: invalid path"
        paths.append(path)
    ui = [path for path in paths if permitted_ui(path)]
    if set(paths) != set(ui + [QUEUE]) or not (1 <= len(ui) <= MAX_UI_FILES):
        return 2, f"FAIL: UI-only allowlist violation: {paths}"
    try:
        subprocess.run(("git", "diff", "--check"), check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError:
        return 2, "FAIL: git diff --check"
    changed = 0
    for line in git("diff", "--numstat", "--", *paths).splitlines():
        parts = line.split("\t")
        if len(parts) != 3 or not parts[0].isdigit() or not parts[1].isdigit():
            return 2, "FAIL: binary or unexpected diff"
        changed += int(parts[0]) + int(parts[1])
    if changed > MAX_CHANGED_LINES:
        return 2, f"FAIL: too many changed lines ({changed})"
    for path in ui:
        p = Path(path)
        if not p.is_file() or p.is_symlink() or p.stat().st_size > 1_000_000:
            return 2, f"FAIL: unsafe output file {path}"
    for line in git("diff", "--unified=0", "--", *ui).splitlines():
        if line.startswith("+") and not line.startswith("+++"):
            if any(token.lower() in line.lower() for token in PROHIBITED_ADDITIONS):
                return 2, "FAIL: prohibited code or formal/result reference added"
    return 0, f"V240_UI_ONLY_GUARD_PASS task={first_pending(old_queue)[0]} files={ui} changed_lines={changed}"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pending", action="store_true")
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    if args.pending:
        task = first_pending(Path(QUEUE).read_text(encoding="utf-8"))
        if task is None:
            print("V240_QUEUE_COMPLETE")
            return 1
        print(f"V240_NEXT_TASK {task[0]}: {task[1]}")
        return 0
    if args.verify:
        code, message = verify()
        print(message)
        return code
    parser.error("specify --pending or --verify")
    return 2


if __name__ == "__main__":
    sys.exit(main())
