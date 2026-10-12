#!/usr/bin/env python3
"""V295 single PRE_RESULT fast lane owner and safe V231 manual relay regression."""
from pathlib import Path
import json
import re
import subprocess

root=Path('.')
wf=(root/'.github/workflows/BOAT_EDGE_V231_BYTE_EXACT_PUBLISH.yml').read_text(encoding='utf8')
v235=(root/'.github/workflows/V235.yml').read_text(encoding='utf8')
v230=(root/'.github/workflows/BOAT_EDGE_V230_FAST_OFFICIAL_PREDEADLINE.yml').read_text(encoding='utf8')
formal=json.loads((root/'data/formal_status.json').read_text(encoding='utf8'))
triggers=wf.split('\npermissions:',1)[0]

assert triggers.count('workflow_dispatch:')==1
for forbidden in ('schedule:', 'cron:', 'workflow_run:', 'push:'):
    assert forbidden not in triggers, ('V295_DUPLICATE_LEGACY_TRIGGER',forbidden)
for forbidden in ('PY_V230_INSTALL','gzip.decompress','base64.b64decode',
                  'git add ', 'git push ', 'git reset ','data/site_results/',
                  '/race/result','/race/pay','results_seen=true','scoring=true'):
    assert forbidden not in wf, ('V295_LEGACY_OR_RESULT_ACCESS',forbidden)
assert 'permissions:\n  contents: read\n  actions: write' in wf
assert 'cancel-in-progress: false' in wf
assert "gh workflow run V235.yml --ref main" in wf
assert wf.count('gh workflow run V235.yml --ref main')==1
assert 'V295_FORMAL_LOCK_UNVERIFIED' in wf and 'V295_FORMAL_FRESH_NOT_PRE_RESULT' in wf
assert 'V295_CURRENT_V230_PIN_MISMATCH' in wf
assert 'V295_CURRENT_V235_DISPATCH_REQUESTED_NOT_ACCURACY_PASS' in wf
assert 'schedule:' in v235 and 'workflow_run:' in v235 and 'workflow_dispatch:' in v235
assert 'schedule:' not in v230.split('\npermissions:',1)[0]
assert 'workflow_dispatch:' in v230.split('\npermissions:',1)[0]

match=re.search(r"'scripts/boat_edge_v230_fast_lane.py:([0-9a-f]{40})'",v235)
assert match, 'V295_V235_PIN_UNAVAILABLE'
actual=subprocess.check_output(['git','hash-object','scripts/boat_edge_v230_fast_lane.py'],text=True).strip()
assert match.group(1)==actual, 'V295_V235_PIN_DRIFT'
g=formal.get('guards') or {}
assert all(g.get(x) is False for x in ('results_seen','unlock','scoring'))
assert g.get('RESULT_UNLOCK_TOKEN') is None
assert (formal.get('formalFirst100') or {}).get('races')==0
print('V295_MANUAL_V231_RELAY_SINGLE_SCHEDULE_OWNER_AND_FORMAL_LOCK_PASS')
