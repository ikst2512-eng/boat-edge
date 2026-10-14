"""V241 must never restore legacy UI on scheduled SITE result refresh.

Static fixture-only: no network, race outcomes, or Formal Fresh access.
"""
from pathlib import Path
import re
import unittest

ROOT=Path(__file__).resolve().parents[1]
WORKFLOW=ROOT/'.github/workflows/v241.yml'
V247=ROOT/'tests/test_boat_edge_v247_ui.cjs'

class V241ReportOnly(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.wf=WORKFLOW.read_text(encoding='utf-8')

    def test_keep_bounded_hourly_result_report_and_main_lock(self):
        wf=self.wf
        self.assertIn("cron: '25 0-14,23 * * *'",wf)
        self.assertIn('workflow_dispatch:',wf)
        self.assertIn("github.ref == 'refs/heads/main'",wf)
        self.assertIn('cancel-in-progress: false',wf)
        self.assertNotIn('  workflow_run:',wf.split('permissions:',1)[0])
        self.assertIn('git reset --hard origin/main',wf)
        self.assertIn('test_boat_edge_v241_results.py',wf)
        self.assertIn('python3 scripts/boat_edge_v241_results.py',wf)
        self.assertIn('V241_REPORT_UNCHANGED_NO_UI_REWRITE',wf)

    def test_no_historical_installer_or_ui_write_path(self):
        wf=self.wf
        for forbidden in (
            'base64.b64decode','gzip.decompress',
            'PY_V241_INSTALL','v241_install.py',
            'V241_EXISTING_RESOURCE_MODIFIED_FAIL_CLOSED',
            'python3 scripts/boat_edge_v241_patch_home.py\n',
            'git add -- results.html index.html',
        ):
            self.assertNotIn(forbidden,wf)
        self.assertIn('V241_TRACKED_SITE_ONLY_NO_LEGACY_REINSTALL_PASS',wf)
        self.assertIn('git diff --exit-code -- index.html results.html',wf)
        self.assertIn('git add -- data/site_autopilot/v241_results_current.json',wf)
        self.assertIn("allowed={'data/site_autopilot/v241_results_current.json'}",wf)
        self.assertIn("V241_STAGED_NON_REPORT_PATH_",wf)
        self.assertNotIn('data/formal_results',wf)
        self.assertNotIn('RESULT_UNLOCK_TOKEN=',wf)

    def test_v247_ui_regression_follows_new_single_writer(self):
        source=V247.read_text(encoding='utf-8')
        self.assertIn('V241_NO_OBSOLETE_UI_REINSTALL_SINGLE_REPORT_WRITER_PASS',source)
        self.assertNotIn('V241_PACKAGED_BYTES_INVALID_',source)
        self.assertIn("assert(!worker.includes('v241_install.py'))",source)
        self.assertTrue((ROOT/'scripts/boat_edge_v241_results.py').is_file())
        self.assertTrue((ROOT/'assets/boat_edge_v241_home.js').is_file())

if __name__=='__main__':
    unittest.main()
