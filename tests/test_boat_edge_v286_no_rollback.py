"""V286: retire obsolete V216 gzip bootstrap, retain prospective safety order."""
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
WORKFLOW=ROOT/'.github/workflows/BOAT_EDGE_V216_SOURCE_DIAGNOSTIC.yml'

class NoPinnedRollback(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.src=WORKFLOW.read_text(encoding='utf-8')
    def test_no_legacy_installer_or_self_modified_code(self):
        src=self.src
        for forbidden in ('PYV216_INSTALL','gzip.decompress','base64.b64decode',
                          'V216_UPGRADED_VERIFIED_V215','file.write_bytes(data)',
                          "git add -- ai-simulation.html scripts/boat_edge_v215_readiness.py"):
            self.assertNotIn(forbidden,src)
        self.assertIn('V286_V265_SOURCE_PIN_AND_FORMAL_LOCK_PASS_NO_REINSTALL',src)
        self.assertIn('V286_SOURCE_PROVENANCE_CHANGED_REVIEW_REQUIRED',src)
        self.assertIn('f74705858e9bffbe28b4ce444d29aa8565ed6497',src)
    def test_freeze_before_grade_order_unmodified(self):
        steps=['Audit upcoming races and persist actual pre-result source deficits',
               'Freeze eligible V214 odds-proof shadow BEFORE results',
               'Continue approved-only daily 50000 yen paper selection BEFORE results',
               'Grade only earlier committed shadow records AFTER freeze',
               'Settle only previously committed paper records']
        offsets=[self.src.index('      - name: '+s) for s in steps]
        self.assertEqual(offsets,sorted(offsets))
        for command in ('python3 scripts/boat_edge_v215_readiness.py',
                        'python3 scripts/boat_edge_v214_shadow.py freeze',
                        'python3 scripts/boat_edge_v211_paper_sim.py select',
                        'python3 scripts/boat_edge_v214_shadow.py settle',
                        'python3 scripts/boat_edge_v211_paper_sim.py settle'):
            self.assertIn(command,self.src)
    def test_schedule_and_formal_lock_retained(self):
        self.assertIn("cron: '4,9,14,19,24,29,34,39,44,49,54,59 * * * *'",self.src)
        self.assertIn("'results_seen','unlock','scoring'",self.src)
        self.assertIn("g['RESULT_UNLOCK_TOKEN'] is None",self.src)
        self.assertIn('node --check assets/boat_edge_v215_readiness.js',self.src)
        self.assertIn("PYTHONPATH=scripts PYTHONDONTWRITEBYTECODE=1 python3 tests/test_boat_edge_v265_readiness_sources.py",self.src)

if __name__=='__main__':
    unittest.main()
