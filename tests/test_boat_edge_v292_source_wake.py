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
def admitted(ev,ref,conclusion=None,branch=None,repo=None,expected='ikst2512-eng/boat-edge'):
    return ref=='refs/heads/main' and (ev!='workflow_run' or (
        conclusion=='success' and branch=='main' and repo==expected))
assert admitted('schedule','refs/heads/main')
assert admitted('workflow_dispatch','refs/heads/main')
assert admitted('workflow_run','refs/heads/main','success','main','ikst2512-eng/boat-edge')
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
print('V292_FAIL_CLOSED_SOURCE_SUCCESS_WAKE_MAIN_ONLY_PASS')
