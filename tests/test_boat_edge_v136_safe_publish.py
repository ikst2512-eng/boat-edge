"""Static contract for V136 SITE-only accuracy conflict retry."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class V136PublishContract(unittest.TestCase):
    def test_recompute_from_main_before_each_publish(self):
        workflow = (ROOT / ".github/workflows/site-v136.yml").read_text()
        publisher = workflow.split(
            "      - name: Publish V136 report only after fresh-main recomputation", 1
        )[1]
        for required in (
            "for attempt in 1 2 3 4; do",
            "git fetch --no-tags origin main",
            "git reset --hard origin/main",
            "python3 scripts/site_accuracy_v136.py",
            "git add -- data/site_learning/mode_accuracy_v136.json",
            "V136_UNEXPECTED_STAGED_PATH_",
            "V136_FRESH_MAIN_SCORE_PUBLISH_BLOCKED",
        ):
            self.assertIn(required, publisher)
        self.assertLess(publisher.index("git reset --hard origin/main"),
                        publisher.index("python3 scripts/site_accuracy_v136.py"))
        self.assertLess(publisher.index("python3 scripts/site_accuracy_v136.py"),
                        publisher.index("git add -- data/site_learning/mode_accuracy_v136.json"))
        self.assertNotIn("git pull --rebase", publisher)
        self.assertNotIn("git push --force", publisher)

    def test_formal_and_model_gates_remain_closed(self):
        workflow = (ROOT / ".github/workflows/site-v136.yml").read_text()
        publisher = workflow.split(
            "      - name: Publish V136 report only after fresh-main recomputation", 1
        )[1]
        self.assertIn("SITE_REFERENCE_POST_SETTLEMENT_ONLY_NOT_FORMAL_FRESH", publisher)
        self.assertIn("d['formal_current_scoring'] is False", publisher)
        self.assertIn("d['production_prediction_weights_changed'] is False", publisher)
        self.assertIn("data/site_learning/site_mode_evaluations_v136/", publisher)
        self.assertNotIn("data/formal_status.json", publisher)


if __name__ == "__main__":
    unittest.main()
