#!/usr/bin/env python3
"""V295 single PRE_RESULT fast lane owner and safe V231 manual relay regression."""
from pathlib import Path
import json
import re
import subprocess

root=Path('.')
# Fully retired V231 may not return as a duplicate Git writer.
assert not (root/'.github/workflows/BOAT_EDGE_V231_BYTE_EXACT_PUBLISH.yml').exists()
v235=(root/'.github/workflows/V235.yml').read_text(encoding='utf8')
v230=(root/'.github/workflows/BOAT_EDGE_V230_FAST_OFFICIAL_PREDEADLINE.yml').read_text(encoding='utf8')
formal=json.loads((root/'data/formal_status.json').read_text(encoding='utf8'))
assert 'schedule:' in v235 and 'workflow_run:' in v235 and 'workflow_dispatch:' in v235
assert 'schedule:' not in v230.split('\npermissions:',1)[0]
assert 'workflow_dispatch:' in v230.split('\npermissions:',1)[0]

assert "'scripts/boat_edge_v230_fast_lane.py:TRACKED_MAIN'" in v235
assert 'git rev-parse "HEAD:$path"' in v235
actual=subprocess.check_output(['git','hash-object','scripts/boat_edge_v230_fast_lane.py'],text=True).strip()
tracked=subprocess.check_output(['git','rev-parse','HEAD:scripts/boat_edge_v230_fast_lane.py'],text=True).strip()
assert tracked==actual, 'V295_V235_GIT_TREE_SOURCE_MISMATCH'
g=formal.get('guards') or {}
assert all(g.get(x) is False for x in ('results_seen','unlock','scoring'))
assert g.get('RESULT_UNLOCK_TOKEN') is None
assert (formal.get('formalFirst100') or {}).get('races')==0
# Other imminent races must be retried just after FIRST Git publication.
first=v235.index("V234_PRE_RESULT_SOURCE_PUBLISH_UNCONFIRMED")
retry=v235.index("      - name: V235 retry other incomplete sources AFTER first immutable Git publication")
scorer=v235.index("      - name: Install evidence-bound scorer and run 35 regressions")
assert first < retry < scorer, 'V295_POSTCOMMIT_RECOVERY_DELAYED_BEHIND_SCORING'
assert "if: env.V235_INITIAL_SNAPSHOT_PUBLISHED == '1'" in v235[retry:scorer]
assert "--postcommit-incomplete" in v235[retry:scorer]
assert "V235_POSTCOMMIT_NO_FROZEN_EVIDENCE_DELETE" in v235[retry:scorer]
print('V295_V231_RETIRED_V235_EARLY_POSTCOMMIT_FORMAL_LOCK_PASS')

