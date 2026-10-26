"""Synthetic read-only inventory controls. No race results."""
import json
import tempfile
import unittest
from pathlib import Path
from inventory_v332_local import inspect

class InventoryV332Tests(unittest.TestCase):
    def test_missing_is_not_success(self):
        with tempfile.TemporaryDirectory() as d:
            x = inspect(d, "20261026")
            self.assertEqual(x["status"], "NO_LOCAL_V332_DIRECTORY")
            self.assertEqual(x["comparable_for_scoring"], 0)

    def test_local_receipt_cannot_authorize_scoring(self):
        with tempfile.TemporaryDirectory() as d:
            folder = Path(d) / "data/research_local_v332/20261026"
            folder.mkdir(parents=True)
            key = "20261026-06-08"
            payload = {"race_key": key, "frozen_at_jst": "2026-10-26T13:59:00+09:00",
                       "deadline_jst": "2026-10-26T14:06:00+09:00",
                       "evidence_level": "LOCAL_RECEIPT_RAW_SHA_ONLY", "scoring_authorized": False}
            (folder / (key + ".json")).write_text(json.dumps(payload))
            x = inspect(d, "20261026")
            self.assertEqual(x["local_receipt_valid"], 1)
            self.assertEqual(x["independently_attested"], 0)
            self.assertEqual(x["comparable_for_scoring"], 0)
            self.assertFalse(x["outcomes_read"])

    def test_result_bearing_record_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            folder = Path(d) / "data/research_local_v332/20261026"
            folder.mkdir(parents=True)
            key = "20261026-06-08"
            (folder / (key + ".json")).write_text(json.dumps({
                "race_key": key, "results": {"unsafe": True}}))
            x = inspect(d, "20261026")
            self.assertEqual(x["local_receipt_valid"], 0)
            self.assertEqual(x["invalid"][0]["reason"], "RESULT_BEARING_RECORD")

if __name__ == "__main__":
    unittest.main()
