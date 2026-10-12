"""V310 synthetic source-coverage tests."""
import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "scripts"))
from boat_edge_v310_source_coverage import source_coverage


def fixture():
    return {"deadline_jst": "2026-10-13T12:00:00+09:00", "captures": [
        {"source": "official", "source_id": "official/race-01",
         "captured_at_jst": "2026-10-13T11:49:00+09:00", "fields": ["actual_course_by_boat"]},
        {"source": "boaters", "source_id": "boaters/race-01",
         "captured_at_jst": "2026-10-13T11:50:00+09:00", "fields": ["strength_by_boat"]},
        {"source": "kyoteibiyori", "source_id": "kyoteibiyori/race-01",
         "captured_at_jst": "2026-10-13T11:51:00+09:00", "fields": ["exhibition"]},
    ]}


class V310SourceCoverage(unittest.TestCase):
    def test_three_sources_pre_deadline(self):
        x = source_coverage(fixture())
        self.assertTrue(x["ready_for_independent_review"])
        self.assertFalse(x["independently_authenticated"])
        self.assertFalse(x["model_promotion_authorized"])

    def test_missing_source_and_late_capture(self):
        x = fixture()
        x["captures"].pop()
        self.assertEqual(source_coverage(x)["missing_sources"], ["kyoteibiyori"])
        x = fixture()
        x["captures"][1]["captured_at_jst"] = "2026-10-13T12:01:00+09:00"
        result = source_coverage(x)
        self.assertIn("boaters", result["missing_sources"])
        self.assertIn("CAPTURE_NOT_BEFORE_DEADLINE", result["reasons"])

    def test_source_id_must_exist(self):
        x = fixture()
        x["captures"][0]["source_id"] = ""
        self.assertFalse(source_coverage(x)["ready_for_independent_review"])


if __name__ == "__main__":
    unittest.main()
