#!/usr/bin/env python3
"""Gate 1C: prevent completion-event cascades among live source pipelines.

A *skipped job* still completes its workflow_run. Rejecting it in a job "if"
does not stop its downstream workflow_run listeners. The event graph itself
must be acyclic to avoid Actions run storms and cron starvation.
No external calls, odds, results, settlement or formal state reads.
"""
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[1]
FILES={
    'collector':'.github/workflows/auto-update.yml',
    'odds':'.github/workflows/site-odds.yml',
    'observer':'.github/workflows/BOAT_EDGE_V216_SOURCE_DIAGNOSTIC.yml',
    'freeze':'.github/workflows/V235.yml',
    'first_git':'.github/workflows/BOAT_EDGE_V229_ATOMIC_FREEZE_AUDIT.yml',
    'pages':'.github/workflows/pages-controlled-publish.yml',
}
content={k:(ROOT/p).read_text(encoding='utf-8') for k,p in FILES.items()}
names={k:re.search(r'(?m)^name:\s*(.*)$',v).group(1).strip() for k,v in content.items()}
edges={k:set() for k in FILES}
for listener,source in content.items():
    preamble=source.split('jobs:',1)[0]
    # Only parse workflow_run.workflows (not branch/cron/path job steps).
    if '  workflow_run:' not in preamble:
        continue
    # Comments split monitored workflow names in V229. Never read only
    # the contiguous list prefix or a reciprocal edge can be missed.
    source_block=preamble.split('  workflow_run:',1)[1].split('    types:',1)[0]
    watched=set(re.findall(r"(?m)^\\s+-\\s+['\\\"]([^'\\\"]+)['\\\"]",source_block))
    for producer,name in names.items():
        if name in watched:
            edges[producer].add(listener)
for node in edges:
    seen=set()
    stack=[]
    def walk(current):
        if current in stack:
            raise AssertionError('GATE1C_WORKFLOW_COMPLETION_CYCLE:'+ ' -> '.join(stack+[current]))
        if current in seen:
            return
        stack.append(current)
        for child in sorted(edges[current]):
            walk(child)
        stack.pop()
        seen.add(current)
    walk(node)
assert 'first_git' in edges['freeze']
assert 'first_git' in edges['observer']
assert 'freeze' in edges['observer']
assert 'observer' in edges['collector']
assert 'observer' in edges['odds']
assert 'collector' in edges['odds']
assert 'first_git' in edges['collector']
assert 'first_git' in edges['odds']
assert 'pages' in edges['first_git']
for key in ('observer','freeze','first_git'):
    assert 'schedule:' in content[key] and 'workflow_dispatch:' in content[key]
for key in ('collector','odds'):
    assert 'schedule:' in content[key] and 'workflow_dispatch:' in content[key]
for key in ('freeze','first_git'):
    assert "github.event.workflow_run.head_repository.full_name == github.repository" in content[key]
    assert "github.event.workflow_run.conclusion == 'success'" in content[key]
assert "V229_NO_NEW_ELIGIBLE_EVIDENCE" in content['first_git']
assert "V71_SOURCE_TIMESTAMP_GUARDED_ODDS_PUBLISHED" in content['odds']
assert "V270_PRE_RESULT_SAFE_PUSH_PASS" in content['collector']
print('GATE1C_SOURCE_WORKFLOW_ACYCLIC_PRE_RESULT_GUARDS_PASS', edges)
