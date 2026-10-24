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


    def test_predeadline_availability_reason_has_distinct_states(self):
        workflow = (Path(__file__).resolve().parents[1] / ".github/workflows/auto-update.yml").read_text(encoding="utf-8")
        for state in ("available", "http_404", "fetch_error", "incomplete_race_row", "race_row_absent"):
            self.assertIn('"' + state + '"', workflow)
        self.assertIn('"observed_at":iso', workflow)
        self.assertIn('"availability_reason":reason', workflow)
        self.assertIn('"source_error":info["error"] if reason=="fetch_error" else None', workflow)
        self.assertLess(workflow.index('if not source_write_allowed(DATA,race_key'), workflow.index('"availability_reason":reason'))


if __name__ == "__main__":
    unittest.main()
