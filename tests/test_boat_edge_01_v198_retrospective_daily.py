"""V198 is a retrospective, source-verified SITE research report, not a live freezer.

Guard its single daily trigger and first-Git-freeze-before-outcome check without
reading any actual result data. Keep a manual rerun for the 02 research owner.
"""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github/workflows/BOAT_EDGE_V198_ROLE_DIAGNOSTIC.yml"


class V198RetrospectiveSchedule(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = WORKFLOW.read_text(encoding="utf-8")
        cls.events = cls.source.split("\non:\n", 1)[1].split("\npermissions:", 1)[0]

    def test_one_daily_report_and_manual_override_only(self):
        self.assertIn("  workflow_dispatch:", self.events)
        self.assertIn("  schedule:", self.events)
        crons = re.findall(r"(?m)^\s+- cron: '([^']+)'", self.events)
        self.assertEqual(crons, ["20 1 * * *"])
        self.assertNotIn("  workflow_run:", self.events)
        self.assertIn("github.ref == 'refs/heads/main'", self.source)

    def test_snapshot_sha_and_first_git_commit_still_precede_site_outcomes(self):
        source = self.source
        verify_index = source.index("verified,reason=scorer.valid_freeze(ROOT,path)")
        if_failed_index = source.index("if reason:", verify_index)
        outcome_index = source.index("result=v185.load_json(ROOT/'data/site_results'", if_failed_index)
        self.assertLess(verify_index, if_failed_index)
        self.assertLess(if_failed_index, outcome_index)
        self.assertIn("result.get('status')!='confirmed'", source)
        self.assertIn("HISTORICAL_BACKFILL_FORBIDDEN", source)
        self.assertIn("'scope':'SITE_REFERENCE_RESEARCH_ONLY_NOT_FORMAL_FRESH'", source)

    def test_only_diagnostic_artifact_is_staged_and_determinism_retained(self):
        src = self.source
        self.assertIn("cmp /tmp/V198_RUN1.json /tmp/V198_RUN2.json", src)
        adds = re.findall(r"(?m)^\s*git add(?: -[^ ]+)* --? ([^\n]+)$", src)
        self.assertEqual(adds, ["data/site_learning/v198_immutable_role_diagnosis.json"])
        self.assertIn("git diff --cached --quiet", src)
        self.assertIn("'no_current_model_change':True,'no_production_promote':True", src)
        self.assertIn("'formal_results_accessed':False,'formal_guard_modified':False", src)
        self.assertNotIn("gh workflow run", src)
        self.assertNotIn("data/formal_results", src)


if __name__ == "__main__":
    unittest.main()
