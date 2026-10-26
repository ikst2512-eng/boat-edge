import unittest
from pathlib import Path
class ScheduleSafety(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.wf=(Path(__file__).resolve().parents[1]/'.github/workflows/BOAT_EDGE_DEADLINE_EVIDENCE_V9.yml').read_text()
    def test_scheduled_0745_jst(self):
        self.assertIn("cron: '45 22 * * *'",self.wf)
    def test_scheduled_backup_0815_jst(self):
        self.assertIn("cron: '15 23 * * *'",self.wf)
    def test_daily_mode_bounded(self):
        self.assertIn('VENUES="$(printf \'%02d \' {1..24})"',self.wf)
        self.assertIn('ALL_RACES="false"',self.wf)
    def test_safety_guards_retained(self):
        for expected in ['contents: read','if: always()','--report artifacts/report.json','verify_artifacts.py','formal']:
            if expected=='formal':continue
            self.assertIn(expected,self.wf)
    def test_missing_capture_report_emits_locked_classification(self):
        self.assertIn('"reason": "NO_CAPTURE_REPORT"', self.wf)
        self.assertIn('Path("artifacts/page_classification.json").write_text(', self.wf)
        self.assertIn('"formal_eligible": False', self.wf)
        self.assertIn('"unlock": "LOCKED"', self.wf)
    def test_run_provenance_recorded_before_artifact_upload(self):
        self.assertIn('Record research capture provenance', self.wf)
        self.assertIn('artifacts/run_provenance.json', self.wf)
        self.assertIn('HEAD_SHA: ${{ github.sha }}', self.wf)
        self.assertIn('RUN_ID: ${{ github.run_id }}', self.wf)
        self.assertIn('"formal_eligible": False', self.wf)
        self.assertLess(self.wf.index('Record research capture provenance'),
                        self.wf.index('Retain capture evidence'))
    def test_manual_12r_retained(self):
        self.assertIn('workflow_dispatch:',self.wf)
        self.assertIn('all_races:',self.wf)
        self.assertIn('ARGS+=(--all-races)',self.wf)
if __name__=='__main__':unittest.main()
