"""Guard the separation of deadline-urgent and post-enrichment cohorts."""
from pathlib import Path
import re
import unittest


class UrgentExhibitionCohortContract(unittest.TestCase):
    def test_distinct_denominators_and_no_overwrite(self):
        workflow = (Path(__file__).resolve().parents[1] / ".github/workflows/auto-update.yml").read_text(encoding="utf-8")
        self.assertIn('"beforeinfo_urgent_15m_targets":len(urgent_keys)', workflow)
        self.assertIn('"original_exhibition_urgent_15m_complete":urgent_original_saved', workflow)
        self.assertIn('"original_exhibition_urgent_15m_missing":urgent_original_missing', workflow)
        self.assertIn("assert urgent_original_saved+urgent_original_missing==len(urgent_keys)", workflow)
        for field, expression in (
            ("original_exhibition_post_enrichment_15m_complete", "complete"),
            ("original_exhibition_post_enrichment_15m_missing", "missing"),
            ("original_exhibition_post_enrichment_15m_targets", "complete+missing"),
        ):
            self.assertIn(f'health["{field}"]={expression}', workflow)
        for field in ("original_exhibition_urgent_15m_complete", "original_exhibition_urgent_15m_missing"):
            self.assertNotRegex(workflow, r'health\["' + re.escape(field) + r'"\]\s*=')


if __name__ == "__main__":
    unittest.main()
