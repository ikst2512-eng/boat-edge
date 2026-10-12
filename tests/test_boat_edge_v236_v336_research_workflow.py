"""V336 isolated scheduled research workflow guardrails (static, offline)."""
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github/workflows/v336-site-research-live-freeze.yml"


class V336WorkflowSafety(unittest.TestCase):
    def test_schedule_and_artifact_retention(self):
        s = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("workflow_dispatch:", s)
        self.assertIn("2,7,12,17,22,27,32,37,42,47,52,57", s)
        self.assertIn("python3 scripts/boat_edge_v334_live_batch_runner.py", s)
        self.assertIn("--capture --window-minutes 15 --max-races 12", s)
        self.assertIn("actions/upload-artifact@v4", s)
        self.assertIn("retention-days: 30", s)
        self.assertIn("data/research_local_v332/", s)
        self.assertIn("data/source_captures/", s)
        # V340 exposes concrete lack-of-coverage rather than 0/0 success.
        self.assertIn("report['run_diagnostic']", s)
        self.assertIn("window['coverage']", s)
        self.assertIn("RESEARCH_REPORT_SAFETY_FLAGS_INVALID", s)
        self.assertIn("'global_uniqueness_verified':False", s)
        self.assertIn("'research_only':True", s)

    def test_no_repo_write_or_formal_unlock(self):
        s = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("contents: read", s)
        self.assertIn("persist-credentials: false", s)
        self.assertIn("github.ref == 'refs/heads/main'", s)
        self.assertIn("RESULT_UNLOCK_TOKEN", s)
        self.assertIn("git status --porcelain --untracked-files=no", s)
        for forbidden in ("contents: write", "git push", "git commit",
                          "resultlist", "payout", "race_result", "gh pr merge"):
            self.assertNotIn(forbidden, s)


if __name__ == "__main__":
    unittest.main()
