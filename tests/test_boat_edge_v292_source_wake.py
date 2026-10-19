#!/usr/bin/env python3
"""V292: additional source-success triggers; no result or formal cohorts inspected."""
from pathlib import Path
import json
s=Path('.github/workflows/BOAT_EDGE_V229_ATOMIC_FREEZE_AUDIT.yml').read_text(encoding='utf8')
assert "name: BOAT EDGE V229 - Atomic Site Freeze and Pre-result Audit" in s
prefix=s.split('jobs:',1)[0]
job=s.split('jobs:',1)[1].split('    runs-on:',1)[0]
assert prefix.count('workflow_run:')==1
assert "'BOAT EDGE 自動更新'" in prefix
assert "'BOAT EDGE 3連単オッズ更新 V71'" in prefix
# Gate 1A: 2026-10-15 source-ready but missed freeze windows. The existing
# V235 source lane is an additional completion signal; it is not a new writer.
v235_name="'BOAT EDGE V235 - Stable Autonomous Prediction Freeze and Verified Scoring'"
assert prefix.count(v235_name) == 1
# Gate 1C: a V216 *scheduled* completion can independently wake V229
# even when V229 and V235 cron is dropped. Collector-triggered V216 events
# must not fan out a duplicate V229, and no new cron/writer is introduced.
v216_name="'BOAT EDGE V216 - Identify Exact Pre-Deadline Source Gaps'"
assert prefix.count(v216_name) == 1
assert "github.event.workflow_run.name != " + v216_name in job
assert "github.event.workflow_run.event == 'schedule'" in job
v216=Path('.github/workflows/BOAT_EDGE_V216_SOURCE_DIAGNOSTIC.yml').read_text(encoding='utf8')
# V229 ORIGINAL SCHEDULE -> V216 adds independent time-window sampling.
# V229 workflow_run -> V216 is blocked; V229 accepts V216 only when the
# upstream V216 event was schedule/dispatch (so there is no event cycle).
v216_event=v216.split('jobs:',1)[0]
v216_job=v216.split('  deadline-audit:',1)[1].split('    runs-on:',1)[0]
assert v216_event.count("'BOAT EDGE V229 - Atomic Site Freeze and Pre-result Audit'")==1
assert v216_event.count('workflow_run:')==1
assert "github.event.workflow_run.name == 'BOAT EDGE V229 - Atomic Site Freeze and Pre-result Audit'" in v216_job
assert "github.event.workflow_run.event == 'schedule'" in v216_job
assert "github.event.workflow_run.conclusion == 'success'" in v216_job
assert "github.event.workflow_run.head_branch == 'main'" in v216_job
assert "github.event.workflow_run.head_repository.full_name == github.repository" in v216_job

def v216_admitted(upstream_name, upstream_event, conclusion='success', branch='main', repo='ikst2512-eng/boat-edge'):
    return (conclusion=='success' and branch=='main' and repo=='ikst2512-eng/boat-edge'
            and (upstream_name in ('BOAT EDGE 自動更新','BOAT EDGE 3連単オッズ更新 V71')
            or (upstream_name in ('BOAT EDGE V235 - Stable Autonomous Prediction Freeze and Verified Scoring',
                                  'BOAT EDGE V229 - Atomic Site Freeze and Pre-result Audit')
                and upstream_event=='schedule')))
assert v216_admitted('BOAT EDGE V229 - Atomic Site Freeze and Pre-result Audit','schedule')
assert not v216_admitted('BOAT EDGE V229 - Atomic Site Freeze and Pre-result Audit','workflow_run')
assert not v216_admitted('BOAT EDGE V229 - Atomic Site Freeze and Pre-result Audit','workflow_dispatch')
assert not v216_admitted('BOAT EDGE V229 - Atomic Site Freeze and Pre-result Audit','schedule',conclusion='failure')
assert not v216_admitted('BOAT EDGE V229 - Atomic Site Freeze and Pre-result Audit','schedule',branch='feature')
assert not v216_admitted('BOAT EDGE V229 - Atomic Site Freeze and Pre-result Audit','schedule',repo='fork/boat-edge')
v235=Path('.github/workflows/V235.yml').read_text(encoding='utf8')
v235_events=v235.split('jobs:',1)[0]
assert "name: BOAT EDGE V235 - Stable Autonomous Prediction Freeze and Verified Scoring" in v235_events
assert "'BOAT EDGE V229 - Atomic Site Freeze and Pre-result Audit'" not in v235_events
assert 'workflow_run:' in v235_events  # existing collector -> V235 -> V229, no cycle
assert 'types: [completed]' in prefix
assert "cron: '6,11,16,21,26,31,36,41,46,51,56 0-14,23 * * *'" in prefix
assert "cron: '1 0-14,23 * * *'" in prefix
assert 'cancel-in-progress: false' in prefix
assert "github.ref == 'refs/heads/main'" in job
assert "github.event_name != 'workflow_run'" in job
assert "github.event.workflow_run.conclusion == 'success'" in job
assert "github.event.workflow_run.head_branch == 'main'" in job
assert "github.event.workflow_run.head_repository.full_name == github.repository" in job
assert 'scripts/boat_edge_v229_atomic_freeze.py' in s
assert "V229_NO_NEW_ELIGIBLE_EVIDENCE" in s
assert "git push origin HEAD:main" in s
# Logical contract of GitHub Actions expression: only successful trusted main
# completions are allowed; scheduled/manual triggers keep their old behavior.
def admitted(ev,ref,conclusion=None,branch=None,repo=None,expected='ikst2512-eng/boat-edge',
             upstream_name=None,upstream_event=None):
    return ref=='refs/heads/main' and (ev!='workflow_run' or (
        conclusion=='success' and branch=='main' and repo==expected and
        (upstream_name!='BOAT EDGE V216 - Identify Exact Pre-Deadline Source Gaps'
         or upstream_event=='schedule')))
assert admitted('schedule','refs/heads/main')
assert admitted('workflow_dispatch','refs/heads/main')
assert admitted('workflow_run','refs/heads/main','success','main','ikst2512-eng/boat-edge')
assert admitted('workflow_run','refs/heads/main','success','main','ikst2512-eng/boat-edge',
                upstream_name='BOAT EDGE V216 - Identify Exact Pre-Deadline Source Gaps',
                upstream_event='schedule')
assert not admitted('workflow_run','refs/heads/main','success','main','ikst2512-eng/boat-edge',
                    upstream_name='BOAT EDGE V216 - Identify Exact Pre-Deadline Source Gaps',
                    upstream_event='workflow_run')
for bad in [
    ('workflow_run','refs/heads/main','failure','main','ikst2512-eng/boat-edge'),
    ('workflow_run','refs/heads/main','cancelled','main','ikst2512-eng/boat-edge'),
    ('workflow_run','refs/heads/main','success','feature','ikst2512-eng/boat-edge'),
    ('workflow_run','refs/heads/main','success','main','fork/boat-edge'),
    ('workflow_run','refs/heads/heads/feature','success','main','ikst2512-eng/boat-edge')
]:
    assert not admitted(*bad),bad
g=json.loads(Path('data/formal_status.json').read_text())['guards']
assert all(g[k] is False for k in ('results_seen','unlock','scoring'))
assert g['RESULT_UNLOCK_TOKEN'] is None
# Gate 1C: protect the independent schedule-only V216 -> V71 odds wake.
# V216 itself listens to V71: its workflow_run completions must NEVER echo
# back into V71. This is an independent odds-source producer, not a predictor.
v71=Path('.github/workflows/site-odds.yml').read_text(encoding='utf8')
v71_event=v71.split('jobs:',1)[0]
v71_job=v71.split('  odds:',1)[1].split('    runs-on:',1)[0]
assert v71_event.count('workflow_run:') == 1
assert v71_event.count("'BOAT EDGE V216 - Identify Exact Pre-Deadline Source Gaps'") == 1
assert v71_event.count('cron: "2,7,12,17,22,27,32,37,42,47,52,57 * * * *"') == 1
for required in (
    "github.ref == 'refs/heads/main'",
    "github.repository == 'ikst2512-eng/boat-edge'",
    "github.event.workflow_run.conclusion == 'success'",
    "github.event.workflow_run.event == 'schedule'",
    "github.event.workflow_run.head_branch == 'main'",
    "github.event.workflow_run.head_repository.full_name == github.repository",
    "github.event.workflow_run.name == 'BOAT EDGE V216 - Identify Exact Pre-Deadline Source Gaps'",
):
    assert required in v71_job, required
assert "V71_FRESHER_SOURCE_ONLY_RECONCILED" in v71
assert "V71_SOURCE_TIMESTAMP_GUARDED_ODDS_PUBLISHED" in v71
assert "bash scripts/boat_edge_v01_first_freeze_nudge.sh" in v71

def v71_admitted(ev,ref,repo,upstream_name=None,upstream_event=None,conclusion=None,
                 upstream_branch=None,upstream_repo=None):
    expected='ikst2512-eng/boat-edge'
    return ref=='refs/heads/main' and repo==expected and (
        ev!='workflow_run' or (
            upstream_name=='BOAT EDGE V216 - Identify Exact Pre-Deadline Source Gaps'
            and upstream_event=='schedule' and conclusion=='success'
            and upstream_branch=='main' and upstream_repo==expected))
assert v71_admitted('schedule','refs/heads/main','ikst2512-eng/boat-edge')
assert v71_admitted('workflow_dispatch','refs/heads/main','ikst2512-eng/boat-edge')
assert v71_admitted('workflow_run','refs/heads/main','ikst2512-eng/boat-edge',
                    upstream_name='BOAT EDGE V216 - Identify Exact Pre-Deadline Source Gaps',
                    upstream_event='schedule',conclusion='success',upstream_branch='main',
                    upstream_repo='ikst2512-eng/boat-edge')
for kw in (
    {'upstream_event':'workflow_run'},
    {'conclusion':'failure'},
    {'upstream_branch':'feature'},
    {'upstream_repo':'fork/boat-edge'},
    {'upstream_name':'BOAT EDGE V229 - Atomic Site Freeze and Pre-result Audit'},
):
    values=dict(upstream_name='BOAT EDGE V216 - Identify Exact Pre-Deadline Source Gaps',
                upstream_event='schedule',conclusion='success',upstream_branch='main',
                upstream_repo='ikst2512-eng/boat-edge')
    values.update(kw)
    assert not v71_admitted('workflow_run','refs/heads/main','ikst2512-eng/boat-edge',**values)
assert not v71_admitted('schedule','refs/heads/feature','ikst2512-eng/boat-edge')
assert not v71_admitted('schedule','refs/heads/main','fork/boat-edge')
print('V292_FAIL_CLOSED_SOURCE_SUCCESS_WAKE_MAIN_ONLY_PASS')
