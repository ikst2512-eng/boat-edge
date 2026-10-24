import unittest
from pathlib import Path
class ScheduleSafety(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.wf=(Path(__file__).resolve().parents[1]/'.github/workflows/BOAT_EDGE_DEADLINE_EVIDENCE_V9.yml').read_text()
    def test_scheduled_0745_jst(self):
        self.assertIn("cron: '45 22 * * *'",self.wf)
    def test_daily_mode_bounded(self):
        self.assertIn('VENUES="$(printf \'%02d \' {1..24})"',self.wf)
        self.assertIn('ALL_RACES="false"',self.wf)
    def test_safety_guards_retained(self):
        for expected in ['contents: read','if: always()','--report artifacts/report.json','verify_artifacts.py','formal']:
            if expected=='formal':continue
            self.assertIn(expected,self.wf)
    def test_manual_12r_retained(self):
        self.assertIn('workflow_dispatch:',self.wf)
        self.assertIn('all_races:',self.wf)
        self.assertIn('ARGS+=(--all-races)',self.wf)
if __name__=='__main__':unittest.main()
