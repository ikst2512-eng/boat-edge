"""V321 fixture SITE baseline readiness and forbidden-file isolation."""
import json
import pathlib
import sys
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "scripts"))
from boat_edge_v321_site_readiness import audit

TICKETS = ["1-2-3","1-2-4","1-2-5","1-2-6","1-3-2",
           "1-3-4","1-3-5","1-3-6","1-4-2","1-4-3"]


def baseline(key):
    return {
        "race_key": key,
        "scope": "SITE_REFERENCE_UNSEEN_PRE_RESULT_ONLY_NOT_FORMAL_FRESH",
        "deadline_jst": "2026-10-13T16:40:00+09:00",
        "evidence_committed_at": "2026-10-13T07:20:00+00:00",
        "formal_results_seen": False, "formal_gate_unlocked": False,
        "production_accuracy_claim": "NOT_PROVEN",
        "real_purchases_authorized": False,
        "model_id": "SITE_REFERENCE_V122",
        "top10": TICKETS,
        "top3": TICKETS[:3],
        "top5": TICKETS[:5],
        "head_top1": "1",
    }


class V321Readiness(unittest.TestCase):
    def test_valid_pre_result_and_missing_shadow(self):
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            folder = root / "data/site_autopilot/v232_cohort"
            folder.mkdir(parents=True)
            (folder / "20261013-22-12.json").write_text(
                json.dumps(baseline("20261013-22-12")), encoding="utf-8")
            # Forbidden formal/result files exist but are never opened.
            formal = root / "data/formal_status.json"
            formal.write_text("NOT_JSON_FORBIDDEN", encoding="utf-8")
            result = audit(root, "20261013")
            self.assertEqual(result["baseline_file_count"], 1)
            self.assertEqual(result["baseline_predeadline_metadata_count"], 1)
            self.assertEqual(result["ready_for_accuracy_scoring_count"], 0)
            self.assertFalse(result["results_read"])
            self.assertFalse(result["formal_fresh_read"])
            self.assertFalse(result["rows"][0]["v318_shadow_present"])

    def test_late_baseline_and_mismatched_filename(self):
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            folder = root / "data/site_autopilot/v232_cohort"
            folder.mkdir(parents=True)
            row = baseline("20261013-22-11")
            (folder / "20261013-22-12.json").write_text(json.dumps(row))
            result = audit(root, "20261013")
            self.assertEqual(result["baseline_predeadline_metadata_count"], 0)
            self.assertEqual(result["rows"][0]["baseline_reasons"], ["FILENAME_RACE_KEY_MISMATCH"])

    def test_no_history_date_guessing(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError):
                audit(pathlib.Path(d), "../20261013")
            self.assertEqual(audit(pathlib.Path(d), "20261013")["baseline_file_count"], 0)


if __name__ == "__main__":
    unittest.main()
