"""Regression guard: first Git publication must precede timely recovery."""
from pathlib import Path
import unittest


class V235PostcommitOrderTests(unittest.TestCase):
    def test_postcommit_recovery_precedes_scorer_and_results(self):
        workflow = (Path(__file__).resolve().parents[1] /
                    ".github/workflows/V235.yml").read_text(encoding="utf-8")
        first = workflow.index("      - name: Immutable pre-result source prediction cohort")
        retry = workflow.index("      - name: V235 retry other incomplete sources AFTER first immutable Git publication")
        scorer = workflow.index("      - name: Install evidence-bound scorer")
        results = workflow.index("      - name: Only after pre-result commit - score")
        self.assertLess(first, retry)
        self.assertLess(retry, scorer)
        self.assertLess(retry, results)
        self.assertEqual(workflow.count("      - name: V235 retry other incomplete sources"), 1)
        # Preserve the verified first-Git publication gate.
        block = workflow[retry:scorer]
        self.assertIn("if: env.V235_INITIAL_SNAPSHOT_PUBLISHED == '1'", block)
        self.assertIn("--postcommit-incomplete", block)
        self.assertIn("git fetch --no-tags origin main", block)
        self.assertIn("git reset --hard origin/main", block)


if __name__ == "__main__":
    unittest.main()
