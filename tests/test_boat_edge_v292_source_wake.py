#!/usr/bin/env python3
"""Gate 1C: prevent completion-event cascades among live source pipelines.

A *skipped job* still completes its workflow_run. Rejecting it in a job "if"
does not stop its downstream workflow_run listeners. The event graph itself
must be acyclic to avoid Actions run storms and cron starvation.
No external calls, odds, results, settlement or formal state reads.
"""
from pathlib import Path
import ast
import re

ROOT=Path(__file__).resolve().parents[1]
FILES={
    'collector':'.github/workflows/auto-update.yml',
    'odds':'.github/workflows/site-odds.yml',
    'observer':'.github/workflows/BOAT_EDGE_V216_SOURCE_DIAGNOSTIC.yml',
    'freeze':'.github/workflows/V235.yml',
    'first_git':'.github/workflows/BOAT_EDGE_V229_ATOMIC_FREEZE_AUDIT.yml',
    'recovery':'.github/workflows/BOAT_EDGE_V220_AUTONOMOUS_SITE_OPERATIONS.yml',
    'pages':'.github/workflows/pages-controlled-publish.yml',
    'browser':'.github/workflows/boat-edge-03-real-browser.yml',
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
    watched=set(re.findall(r"(?m)^\s+-\s+['\"]([^'\"]+)['\"]",source_block))
    for producer,name in names.items():
        if name in watched:
            edges[producer].add(listener)
# V220 can dispatch original producers and V216/V229, not merely listen
# for completions. Include these indirect edges before detecting cycles:
# otherwise V216 -> V220 -> V216 can escape a completion-only graph audit.
ops=(ROOT/'scripts/boat_edge_v220_site_ops.py').read_text(encoding='utf-8')
approved=re.search(r'(?s)\bRECOVER_ALLOW\s*=\s*(\{[^}]*\})',ops)
assert approved, 'GATE1C_RECOVERY_ALLOWLIST_NOT_FOUND'
allowed=ast.literal_eval(approved.group(1))
assert allowed=={
    'auto-update.yml',
    'site-odds.yml',
    'BOAT_EDGE_V216_SOURCE_DIAGNOSTIC.yml',
    'BOAT_EDGE_V229_ATOMIC_FREEZE_AUDIT.yml',
}, 'GATE1C_RECOVERY_ALLOWLIST_CHANGED_REVIEW_REQUIRED'
assert 'gh workflow run "$wf" --ref main' in content['recovery']
keys_by_file={Path(p).name:k for k,p in FILES.items()}
for workflow in allowed:
    assert workflow in keys_by_file, 'GATE1C_UNKNOWN_RECOVERY_DISPATCH_'+workflow
    edges['recovery'].add(keys_by_file[workflow])

# V216 can now call the existing guarded nudge IN its original schedule
# rather than subscribing V229 to V216 completed events. Represent the
# indirect dispatch edge separately and reject future completion feedback.
observer_schedule=content['observer']
assert 'first_git' not in edges['observer'], 'GATE1C_V216_COMPLETION_FANOUT_REINTRODUCED'
assert "      - name: Recover source-ready first Git freeze during independent V216 cron" in observer_schedule
nudge_step=observer_schedule.split(
    '      - name: Recover source-ready first Git freeze during independent V216 cron',1
)[1].split('      - name:',1)[0]
assert "if: github.event_name == 'schedule'" in nudge_step
assert 'bash scripts/boat_edge_v01_first_freeze_nudge.sh' in nudge_step
nudge_source=(ROOT/'scripts/boat_edge_v01_first_freeze_nudge.sh').read_text(encoding='utf-8')
assert 'gh workflow run "$wf" --ref main' in nudge_source
assert 'V229_ALREADY_ACTIVE' in nudge_source
edges['observer'].add('first_git')

# V125 listens to V229 for index auditing, but is permitted to dispatch
# V229 ONLY on V125's independent schedule. Model the event qualification
# explicitly: a V229 completion produces V125.workflow_run, never V125.schedule.
v125=(ROOT/'.github/workflows/site-v125.yml').read_text(encoding='utf-8')
v125_events=v125.split('jobs:',1)[0]
assert 'BOAT EDGE V229 - Atomic Site Freeze and Pre-result Audit' in v125_events
assert '  workflow_run:' in v125_events and '  schedule:' in v125_events
step_name='      - name: Gate 1C independent-schedule source-ready V229 first-freeze wake'
assert v125.count(step_name)==1
v125_nudge=v125.split(step_name,1)[1].split('      - name:',1)[0]
assert "if: github.event_name == 'schedule'" in v125_nudge, 'GATE1C_V125_EVENT_FEEDBACK_RISK'
assert 'bash scripts/boat_edge_v01_first_freeze_nudge.sh' in v125_nudge
assert 'GH_TOKEN: ${{ github.token }}' in v125_nudge
assert '  actions: write' in v125_events
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
# V235 already executes the V230 lane which imports and runs the same
# V229 atomic_freeze in-process. A second V229 workflow_run on V235
# completion adds no original-source opportunity but may starve cron slots.
assert 'first_git' not in edges['freeze']
v230=(ROOT/'scripts/boat_edge_v230_fast_lane.py').read_text(encoding='utf-8')
assert 'from boat_edge_v229_atomic_freeze import run as atomic_freeze' in v230
assert 'count=atomic_freeze(root)' in v230
# No V216 completion subscriber: a skipped job still produces 'completed'.
for target in ('freeze','recovery'):
    assert target not in edges['observer'], (target, edges)
assert edges['recovery']=={'collector','odds','observer','first_git'}
assert 'recovery' not in edges['observer']
assert 'first_git' in edges['observer']
assert 'observer' in edges['collector']
assert 'observer' in edges['odds']
assert 'collector' in edges['odds']
assert 'first_git' in edges['collector']
assert 'first_git' in edges['odds']
assert 'pages' in edges['first_git']
# Read-only browser checks remain independent: a skipped V229 completion is
# never proof of newly frozen evidence and must not spawn Chromium/WebKit.
assert 'browser' not in edges['first_git']
browser_events=content['browser'].split('jobs:',1)[0]
assert '  workflow_run:' not in browser_events
assert '  workflow_dispatch:' in browser_events
assert '  pull_request:' in browser_events
assert '  push:' in browser_events
assert browser_events.count('    - cron:')==3
assert 'contents: read' in browser_events
assert '  schedule:' in browser_events
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
