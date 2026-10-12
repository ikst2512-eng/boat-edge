#!/usr/bin/env python3
"""V289 source-only published readiness and UI wording contract."""
from pathlib import Path
import json
import re
report=Path('scripts/boat_edge_v220_site_ops.py').read_text(encoding='utf8')
html=Path('autopilot.html').read_text(encoding='utf8')
assert "'partial_six_boat_source':urgent_partial if urgent_telemetry_ok else None" in report
assert 'urgent_partial<=urgent_counts[2]' in report
assert "urgent_counts[0]==sum(urgent_counts[1:])" in report
assert "partial_valid and all(type(v) is int" in report
assert html.count('id="officialWindowEvidenceV289"')==1
for token in ("official?.status==='OBSERVED'","official.targets===0",
              "'／うち一部のみ取得 '","put('officialWindowEvidenceV289',officialText)"):
    assert token in html, token
assert '締切15分前の監視対象なし' in html
assert '一部取得' in html
g=json.loads(Path('data/formal_status.json').read_text(encoding='utf8'))['guards']
assert all(g[k] is False for k in ('results_seen','unlock','scoring'))
assert g['RESULT_UNLOCK_TOKEN'] is None
print('V289_OFFICIAL_SOURCE_COUNTERS_AND_UI_FAIL_CLOSED_PASS')
