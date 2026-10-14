"""V198 is a retrospective, source-verified SITE research report, not a live freezer.

After the original pre-deadline Git proof failed in run 38635773633,
retain manual research without automated failures. No result data is opened.
"""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github/workflows/BOAT_EDGE_V198_ROLE_DIAGNOSTIC.yml"


class V198QuarantinedManualResearch(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = WORKFLOW.read_text(encoding="utf-8")
        cls.events = cls.source.split("\non:\n", 1)[1].split("\npermissions:", 1)[0]

    def test_unsafe_repeated_research_is_manual_only(self):
        self.assertIn("  workflow_dispatch:", self.events)
        self.assertNotIn("  schedule:", self.events)
        self.assertNotIn("  push:", self.events)
        self.assertNotIn("  workflow_run:", self.events)
        self.assertEqual(re.findall(r"(?m)^\s+- cron:", self.events), [])
        self.assertIn("github.ref == 'refs/heads/main'", self.source)
        self.assertIn("20261013-12-07", self.source)
        self.assertIn("38635773633", self.source)
        self.assertIn("V198_INVALID_SOURCE_NO_REPORT_PUBLISH", self.source)
        self.assertIn("raise SystemExit(3)", self.source)

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
