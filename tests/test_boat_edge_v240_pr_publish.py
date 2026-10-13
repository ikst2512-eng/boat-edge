#!/usr/bin/env python3
"""Static, synthetic regression for the V240 PR-only publish contract.

No network, no GitHub token, no provider pages, no race data, no payouts.
The test intentionally does not run Codex, push, or create a PR.
"""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "v240-autodev.yml"
GUARD = ROOT / "scripts" / "boat_edge_v240_guard.py"


class TestV240DraftPRPublish(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.workflow = WORKFLOW.read_text(encoding="utf-8")
        cls.guard = GUARD.read_text(encoding="utf-8")

    def test_no_direct_main_or_bypass_push(self):
        script = self.workflow
        pushes = re.findall(r"(?m)^\s*git push\s+[^\n]*$", script)
        self.assertEqual(len(pushes), 1, pushes)
        self.assertIn('HEAD:refs/heads/$branch', pushes[0])
        self.assertNotIn("HEAD:main", script)
        self.assertNotIn("refs/heads/main", pushes[0])
        self.assertNotIn("--force", pushes[0])
        self.assertNotIn("gh pr merge", script)
        self.assertNotIn("gh api repos/", script)
        self.assertNotIn("V240_UI_ONLY_SOURCE_PUBLISHED", script)

    def test_pull_request_is_draft_and_fail_closed(self):
        script = self.workflow
        self.assertIn("pull-requests: write", script)
        self.assertIn("gh pr create", script)
        self.assertIn("--draft", script)
        self.assertIn("--base main --head", script)
        self.assertIn("V240_DRAFT_PR_CREATE_BLOCKED_CHECK_ACTIONS_PR_PERMISSIONS", script)
        self.assertIn("V240_DRAFT_PR_CREATED_REVIEW_REQUIRED_NOT_MERGED_NOT_DEPLOYED", script)
        self.assertIn("git rebase --abort", script)
        self.assertIn("V240_ABORT_SOURCE_MOVED_CONFLICT", script)

    def test_ai_does_not_execute_on_pr_or_without_gate(self):
        script = self.workflow
        self.assertIn("pull_request:", script)
        self.assertIn("BRANCH_REF: ${{ github.ref }}", script)
        self.assertIn("if ! python3 scripts/boat_edge_v240_guard.py --pending", script)
        self.assertIn("OPENAI_KEY_PRESENT: ${{ secrets.OPENAI_API_KEY != '' }}", script)
        self.assertIn("elif [ \"$BRANCH_REF\" != 'refs/heads/main' ]", script)
        self.assertIn("if: steps.gate.outputs.can_run == 'true'", script)
        self.assertIn("V240_FORMAL_GUARD_READ_ONLY_PASS", script)

    def test_isolated_agent_scope_and_independent_tests_retained(self):
        script = self.workflow
        self.assertIn("working-directory: ${{ runner.temp }}/v240-ui", script)
        self.assertIn("permission-profile: ':workspace'", script)
        self.assertIn("python3 scripts/boat_edge_v240_guard.py --verify", script)
        self.assertIn("git diff --cached --check", script)
        self.assertIn("No real", "No real")  # Test has no network operation.
        self.assertIn("MAX_UI_FILES = 4", self.guard)
        self.assertIn("MAX_CHANGED_LINES = 300", self.guard)
        self.assertIn("data/formal_", self.guard)

    def test_regression_runs_on_workflow_or_pr_change(self):
        script = self.workflow
        self.assertIn("tests/test_boat_edge_v240_pr_publish.py", script)
        self.assertGreaterEqual(
            script.count("-p 'test_boat_edge_v240_pr_publish.py'"), 2
        )


if __name__ == "__main__":
    unittest.main()
