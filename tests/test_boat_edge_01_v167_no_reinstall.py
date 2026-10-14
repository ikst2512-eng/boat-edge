"""V167 official 120-odds audit must not reinstall obsolete verifier bytes.

Read-only code/fixture assertions; does not retrieve betting results or odds.
"""
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
WORKFLOW=ROOT/'.github'/'workflows'/'BOAT_EDGE_V167_ONE_UPLOAD.yml'

class V167CurrentAuditor(unittest.TestCase):
    def test_no_legacy_restore_and_keep_independent_audit(self):
        s=WORKFLOW.read_text(encoding='utf-8')
        self.assertIn("cron: '11 0-13 * * *'",s)
        self.assertIn('workflow_dispatch:',s)
        self.assertIn('V167_TRACKED_AUDITOR_NO_LEGACY_REINSTALL_PASS',s)
        self.assertIn('git ls-files --error-unmatch',s)
        self.assertNotIn('base64.b64decode',s)
        self.assertNotIn('gzip.decompress',s)
        self.assertNotIn('.write_bytes(',s)
        self.assertIn('Run offline structural mapping regression tests',s)
        self.assertIn('Assert deployed official odds guard stays active',s)
        self.assertIn('Recheck V167 source',s)
        self.assertIn('site_odds_v167_live_audit.py',s)
        self.assertIn('data/site_odds/verification_v167.json',s)
        self.assertIn("github.ref == 'refs/heads/main'",s)

    def test_tracked_live_verifier_and_regressions_present(self):
        for p in (
            'scripts/site_odds_v167_dom_verifier.py',
            'scripts/site_odds_v167_live_audit.py',
            'tests/test_site_odds_v167.py',
            'tests/test_site_odds_v167_runner.py',
        ):
            with self.subTest(path=p):
                self.assertTrue((ROOT/p).is_file(),p)

if __name__=='__main__':
    unittest.main()
