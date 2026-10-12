#!/usr/bin/env python3
"""V296: neither old V230 nor V233 may re-install stale embedded models."""
from pathlib import Path
import json
import re
import subprocess

root=Path('.')
latest=(root/'.github/workflows/V235.yml').read_text(encoding='utf8')
snapshot=json.loads((root/'data/formal_status.json').read_text(encoding='utf8'))
g=snapshot.get('guards') or {}
assert all(g.get(x) is False for x in ('results_seen','unlock','scoring'))
assert g.get('RESULT_UNLOCK_TOKEN') is None
assert (snapshot.get('formalFirst100') or {}).get('races')==0
match=re.search(r"'scripts/boat_edge_v230_fast_lane.py:([0-9a-f]{40})'",latest)
assert match
actual=subprocess.check_output(['git','hash-object','scripts/boat_edge_v230_fast_lane.py'],text=True).strip()
assert match.group(1)==actual
assert 'workflow_dispatch:' in latest and 'schedule:' in latest and 'workflow_run:' in latest

for path in ('.github/workflows/BOAT_EDGE_V230_FAST_OFFICIAL_PREDEADLINE.yml',
             '.github/workflows/V233.yml'):
    src=(root/path).read_text(encoding='utf8')
    header=src.split('\npermissions:',1)[0]
    assert header.count('workflow_dispatch:')==1
    for forbidden in ('schedule:', 'cron:', 'push:', 'workflow_run:'):
        assert forbidden not in header,(path,forbidden)
    for forbidden in ('PY_V230_INSTALL','gzip.decompress','base64.b64decode',
                     'file.write_bytes','git push','git add','git reset',
                     '/race/result','/race/pay','data/site_results'):
        assert forbidden not in src,(path,forbidden)
    assert 'permissions:\n  contents: read\n  actions: write' in src
    assert 'cancel-in-progress: false' in src
    assert 'V296_CURRENT_V235_PIN_OR_MANUAL_TRIGGER_NOT_VERIFIED' in src
    assert 'V296_FORMAL_LOCK_UNVERIFIED' in src
    assert 'V296_FORMAL_FRESH_NOT_PRE_RESULT' in src
    assert 'V296_CURRENT_V230_PIN_MISMATCH' in src
    assert 'gh workflow run V235.yml --ref main' in src
    assert src.count('gh workflow run V235.yml --ref main')==1
    assert 'V296_CURRENT_V235_DISPATCH_REQUESTED_NOT_ACCURACY_PASS' in src
    assert "github.ref == 'refs/heads/main'" in src
print('V296_LEGACY_V230_V233_NO_REINSTALL_MANUAL_V235_ONLY_PASS')
