from pathlib import Path
import unittest


class V351ScheduledEvidence(unittest.TestCase):
    def test_read_only_scheduled_evidence(self):
        workflow = Path(".github/workflows/boat-edge-v350-actions-evidence.yml").read_text()
        self.assertIn("cron: '23 3 * * *'", workflow)
        self.assertIn("MAX_PAGES: ${{ inputs.max_pages || '3' }}", workflow)
        self.assertIn("actions: read", workflow)
        self.assertIn("contents: read", workflow)
        self.assertIn("persist-credentials: false", workflow)
        self.assertNotIn("git push", workflow)
        self.assertNotIn("contents: write", workflow)


if __name__ == "__main__":
    unittest.main()
