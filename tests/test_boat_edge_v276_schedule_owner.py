#!/usr/bin/env python3
"""V276: source-only audit that the pinned V230 fast lane has ONE scheduled owner.

Does not run the collector, inspect results, payoffs, odds, or formal prediction files.
"""
from pathlib import Path

v230=Path('.github/workflows/BOAT_EDGE_V230_FAST_OFFICIAL_PREDEADLINE.yml').read_text(encoding='utf-8')
v235=Path('.github/workflows/V235.yml').read_text(encoding='utf-8')
fast=Path('scripts/boat_edge_v230_fast_lane.py').read_text(encoding='utf-8')
tr230=v230.split('\npermissions:',1)[0]
tr235=v235.split('\npermissions:',1)[0]

assert 'workflow_dispatch:' in tr230, 'Manual recovery of V230 must stay enabled'
assert 'schedule:' not in tr230 and 'cron:' not in tr230, 'V230 MUST NOT race scheduled V235'
assert 'schedule:' in tr235
assert "cron: '2,7,12,17,22,27,32,37,42,47,52,57 0-14,23 * * *'" in tr235
assert 'workflow_dispatch:' in tr235
assert "python3 scripts/boat_edge_v230_fast_lane.py" in v235
assert "python3 scripts/boat_edge_v232_pre_result_cohort.py" in v235
assert 'git fetch --no-tags origin main' in v235
assert 'git reset --hard origin/main' in v235
assert 'V234_CONCURRENT_GIT_UPDATE_ABANDON_LOCAL_PREDICTIONS' in v235
assert 'cancel-in-progress: false' in v235
assert 'if (root/\'data/site_prediction_snapshots\'/f\'{key}.json\').is_file():continue' in fast
assert 'check_formal_closed(root)' in fast
assert 'V229' in fast and 'atomic_freeze(root)' in fast
assert 'results_seen' in fast and 'scoring' in fast
print('V276_SINGLE_FAST_SOURCE_SCHEDULE_OWNER_PASS')
