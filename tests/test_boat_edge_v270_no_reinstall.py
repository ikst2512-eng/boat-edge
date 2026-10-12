#!/usr/bin/env python3
"""V270: prevent scheduled workflow from restoring obsolete embedded code."""
from pathlib import Path
w=Path('.github/workflows/BOAT_EDGE_V220_AUTONOMOUS_SITE_OPERATIONS.yml').read_text()
assert 'Install pinned site-operations' not in w
assert 'PY_V220_INSTALL' not in w
assert 'gzip.decompress' not in w
assert 'git reset --hard origin/main' in w  # report step still refreshes checkout
assert 'python3 tests/test_boat_edge_v220_site_ops.py' in w
assert 'python3 scripts/boat_edge_v220_site_ops.py' in w
assert 'test -f index.html' in w
assert 'RECOVER_ALLOW' in Path('scripts/boat_edge_v220_site_ops.py').read_text()
assert "odds_120_incomplete" in Path('scripts/boat_edge_v220_site_ops.py').read_text()
assert "official_beforeinfo_source_status" in Path('scripts/boat_edge_v220_site_ops.py').read_text()
print('V270_NO_OBSOLETE_SITE_OPS_REINSTALL_PASS')
