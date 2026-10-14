"""V219 live validation must not restore embedded historical code.

Fixture/source-only checks. No formal results, settlement or network access.
"""
from pathlib import Path
import re
import unittest

ROOT=Path(__file__).resolve().parents[1]
WORKFLOW=ROOT/'.github/workflows/BOAT_EDGE_V219_AUTONOMOUS_VALIDATION.yml'
PAGE=ROOT/'ai-simulation.html'


class V219TrackedSources(unittest.TestCase):
    def test_retired_reinstaller_and_no_automatic_ui_source_rewrite(self):
        source=WORKFLOW.read_text(encoding='utf-8')
        self.assertIn('Verify tracked validation runner and dashboard without legacy reinstall',source)
        self.assertIn('V219_TRACKED_MAIN_SOURCE_ONLY_NO_LEGACY_INSTALL_PASS',source)
        self.assertNotIn('PYV219_INSTALL',source)
        self.assertNotIn('base64.b64decode',source)
        self.assertNotIn('gzip.decompress',source)
        self.assertNotIn('V219_EXISTING_ASSET_CONFLICT_FAIL_CLOSED',source)
        self.assertNotIn('git add -- scripts/boat_edge_autovalidation.py',source)
        self.assertNotIn("page.write_text(",source)
        self.assertNotIn("path.write_bytes(",source)
        self.assertIn('git diff --exit-code -- scripts/boat_edge_autovalidation.py',source)

    def test_keep_live_validation_and_only_evidence_publication(self):
        source=WORKFLOW.read_text(encoding='utf-8')
        self.assertIn("cron: '17,47 * * * *'",source)
        self.assertIn('workflow_dispatch:',source)
        self.assertIn("github.ref == 'refs/heads/main'",source)
        self.assertIn('python3 tests/test_boat_edge_autovalidation.py',source)
        self.assertIn('python3 scripts/boat_edge_autovalidation.py --dry-run',source)
        self.assertIn('python3 scripts/boat_edge_autovalidation.py',source)
        self.assertIn('git add -- data/site_autovalidation/current.json data/site_autovalidation/daily/',source)
        self.assertIn('V219_REPORT_UNCHANGED_NO_SPURIOUS_COMMIT',source)
        self.assertIn('V219_REPORT_PUBLISHED_NO_FORMAL_UNLOCK',source)
        self.assertNotIn('data/formal_results',source)
        self.assertNotIn('RESULT_UNLOCK_TOKEN=',source)

    def test_published_dashboard_uses_current_tracked_sources(self):
        page=PAGE.read_text(encoding='utf-8')
        for resource in (
            'boat_edge_v213_shadow.js',
            './assets/boat_edge_autovalidation.css?v=219',
            './assets/boat_edge_autovalidation.js?v=219',
        ):
            self.assertEqual(page.count(resource),1,resource)
        for file in (
            'scripts/boat_edge_autovalidation.py',
            'tests/test_boat_edge_autovalidation.py',
            'assets/boat_edge_autovalidation.js',
            'assets/boat_edge_autovalidation.css',
        ):
            self.assertTrue((ROOT/file).is_file(),file)


if __name__=='__main__':
    unittest.main()
