"""V238 must not reinstall obsolete source/HTML or stage code from an hourly job.

Static, fixture-only regression: protects current source, report writer, formal lock.
"""
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
PATH=ROOT/'.github/workflows/v238.yml'


class V238TrackedOnly(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.workflow=PATH.read_text(encoding='utf-8')

    def test_no_embedded_old_installer_or_automatic_source_overwrite(self):
        source=self.workflow
        self.assertIn('V238_TRACKED_CURRENT_SOURCE_NO_REINSTALL_PASS',source)
        self.assertNotIn('V238_PACKAGED_RESOURCE_INSTALLED',source)
        for forbidden in ('v238_install.py','gzip.decompress','base64.b64decode',
                          'dest.write_bytes','V238_EXISTING_SOURCE_DRIFT_FAIL_CLOSED',
                          "git add -- scripts/boat_edge_v238_tail_diagnostic.py",
                          "git add -A -- scripts/boat_edge_v238_tail_diagnostic.py"):
            self.assertNotIn(forbidden,source)
        self.assertIn('git ls-files --error-unmatch',source)
        self.assertIn("git diff --exit-code -- scripts/boat_edge_v238_tail_diagnostic.py",source)

    def test_keep_diagnostic_run_and_stage_only_generated_report(self):
        source=self.workflow
        self.assertIn("cron: '17 0-14,23 * * *'",source)
        self.assertIn('workflow_dispatch:',source)
        self.assertIn('git reset --hard origin/main',source)
        self.assertIn("python3 -m unittest discover -s tests -p 'test_boat_edge_v238_tail_diagnostic.py'",source)
        self.assertIn('python3 scripts/boat_edge_v238_tail_diagnostic.py',source)
        self.assertIn('git add -- data/site_autopilot/v238_current.json',source)
        self.assertIn("allowed={'data/site_autopilot/v238_current.json'}",source)
        self.assertNotIn("data/formal_results",source)
        self.assertNotIn("RESULT_UNLOCK_TOKEN=",source)

    def test_existing_diagnostic_files_are_present(self):
        for path in ('scripts/boat_edge_v238_tail_diagnostic.py',
                     'tests/test_boat_edge_v238_tail_diagnostic.py',
                     'tail-diagnostics.html'):
            with self.subTest(path=path):
                self.assertTrue((ROOT/path).is_file())


if __name__=='__main__':
    unittest.main()
