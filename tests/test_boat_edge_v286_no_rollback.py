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
    def test_atomic_pre_result_receipt_before_grade_and_settlement(self):
        steps=['Freeze PRE_RESULT diagnostics and shadow evidence in one Git commit',
               'Continue approved-only daily 50000 yen paper selection BEFORE results',
               'Settle earlier frozen shadow and paper ledgers in one Git commit']
        offsets=[self.src.index('      - name: '+s) for s in steps]
        self.assertEqual(offsets,sorted(offsets))
        commands=('python3 scripts/boat_edge_v215_readiness.py',
                  'python3 scripts/boat_edge_v214_shadow.py freeze',
                  'python3 scripts/boat_edge_v211_paper_sim.py select',
                  'python3 scripts/boat_edge_v214_shadow.py settle',
                  'python3 scripts/boat_edge_v211_paper_sim.py settle')
        for command in commands:
            self.assertIn(command,self.src)
        command_offsets=[self.src.index(c) for c in commands]
        self.assertEqual(command_offsets,sorted(command_offsets))
        early=self.src[offsets[0]:offsets[1]]
        self.assertEqual(early.count('git commit -m'),1)
        self.assertIn('git push origin HEAD:main',early)
        self.assertLess(early.index('V216_FORMAL_RESULT_UNSEEN_GUARD_BLOCKED'),
                        early.index('git commit -m'))
        self.assertNotIn('scripts/boat_edge_v214_shadow.py settle',early)
        self.assertNotIn('scripts/boat_edge_v211_paper_sim.py settle',early)
        self.assertNotIn('data/site_results/',early)
        # Pre-result frozen decisions are first pushed in their own receipt.
        # Only a later SITE-only step may read already-committed results.
        settled=self.src[offsets[2]:]
        self.assertLess(self.src.index('git push origin HEAD:main'),
                        self.src.index('python3 scripts/boat_edge_v214_shadow.py settle'))
        self.assertIn("V216_SETTLE_FORMAL_FRESH_GUARD_BLOCKED", settled)
        self.assertIn("V216_SETTLEMENT_FORBIDDEN_STAGED_FILES_", settled)
        self.assertLess(settled.index('scripts/boat_edge_v214_shadow.py settle'),
                        settled.index('scripts/boat_edge_v211_paper_sim.py settle'))
        self.assertLess(settled.index('scripts/boat_edge_v211_paper_sim.py settle'),
                        settled.index("git commit -m"))
        self.assertEqual(settled.count("git commit -m"),1)
        self.assertEqual(settled.count("git push origin HEAD:main"),1)
        self.assertEqual(self.src.count("git commit -m"),3)

    def test_schedule_and_formal_lock_retained(self):
        # Three disjoint cron groups preserve every 5m pre-result window.
        import re
        crons=re.findall(r"^\\s+- cron: '([^']+)'$",self.src,re.MULTILINE)
        self.assertEqual(len(crons),3)
        minutes=[]
        for cron in crons:
            fields=cron.split()
            self.assertEqual(fields[1:],["*","*","*","*"])
            minutes.extend(int(m) for m in fields[0].split(","))
        self.assertEqual(sorted(minutes),list(range(4,60,5)))
        self.assertEqual(len(minutes),len(set(minutes)))
        settle=self.src.split("      - name: Settle earlier frozen shadow and paper ledgers in one Git commit",1)[1]
        self.assertIn("github.event.schedule == '14,29,44,59 * * * *'",settle)
        self.assertIn("github.event_name != 'schedule'",settle)
        self.assertIn("'results_seen','unlock','scoring'",self.src)
        self.assertIn("g['RESULT_UNLOCK_TOKEN'] is None",self.src)
        self.assertIn('node --check assets/boat_edge_v215_readiness.js',self.src)
        self.assertIn("PYTHONPATH=scripts PYTHONDONTWRITEBYTECODE=1 python3 tests/test_boat_edge_v265_readiness_sources.py",self.src)

if __name__=='__main__':
    unittest.main()
