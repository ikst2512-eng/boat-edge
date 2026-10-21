#!/usr/bin/env python3
"""Read-only check of BOAT EDGE Actions workflow_run dependencies.

No GitHub API, no new workflow triggers, no production writes.
Prints duplicate consumers and fails on completion-trigger cycles.
"""
from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from pathlib import Path


def inventory(directory: Path) -> dict:
    names = {}
    contents = {}
    for path in sorted(list(directory.glob("*.yml")) + list(directory.glob("*.yaml"))):
        source = path.read_text(encoding="utf-8")
        match = re.search(r"(?m)^name:\s*['\"]?([^'\"\r\n]+)", source)
        if match:
            names[match.group(1).strip()] = str(path)
            contents[match.group(1).strip()] = source
    edges = []
    for consumer, source in contents.items():
        match = re.search(r"(?ms)^  workflow_run:\s*\n(.*?)(?=^  [A-Za-z_][\w-]*:|\Z)", source)
        if not match:
            continue
        section = match.group(1)
        target = re.search(r"(?ms)^    workflows:\s*\n((?:^      - .*\n?)+)", section)
        if not target:
            continue
        for item in re.findall(r"(?m)^      -\s*['\"]?(.+?)['\"]?\s*$", target.group(1)):
            producer = item.strip().split(" #", 1)[0].strip().strip("'\"")
            edges.append((producer, consumer))
    graph = defaultdict(list)
    consumers = defaultdict(list)
    for producer, consumer in edges:
        graph[producer].append(consumer)
        consumers[producer].append(consumer)
    cycles = []
    visited = set()
    def visit(node, stack):
        if node in stack:
            cycles.append(stack[stack.index(node):] + [node])
            return
        if node in visited:
            return
        for next_node in graph[node]:
            if next_node in names:
                visit(next_node, stack + [node])
        visited.add(node)
    for node in names:
        visit(node, [])
    unique_cycles = sorted({tuple(cycle) for cycle in cycles})
    return {
        "workflow_files": len(names),
        "completion_edges": len(edges),
        "unknown_producers": sorted(set(producer for producer, _ in edges if producer not in names)),
        "multiple_completion_consumers": {p: sorted(set(c)) for p, c in sorted(consumers.items()) if len(set(c)) > 1},
        "completion_cycles": [list(c) for c in unique_cycles],
        "notes": "Static inventory only; no runtime skip/cancel or missed-freeze proof",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workflows", type=Path, default=Path(".github/workflows"))
    args = parser.parse_args()
    if not args.workflows.is_dir():
        parser.error("missing workflow directory")
    output = inventory(args.workflows)
    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 1 if output["completion_cycles"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
