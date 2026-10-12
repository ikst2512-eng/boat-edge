"""V318 synthetic tests: immutable, predeadline and fail-closed."""
from datetime import datetime, timezone, timedelta
import pathlib
import sys
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "scripts"))
from boat_edge_v318_shadow_freeze import build_freeze, freeze_file

JST = timezone(timedelta(hours=9))


def inputs():
    key = "20261013-22-12"
    report = {
        "ready_for_research_review": True,
        "bundle": {"race_key": key, "deadline_jst": "2026-10-13T16:40:00+09:00"},
        "evidence_audit": {"all_three_document_bundles_consistent": True},
    }
    candidate = {
        "race_key": key, "model_id": "V312_SYNTHETIC",
        "production_eligible": False, "scoring_authorized": False,
        "calibrated": False, "improvement_proven": False,
        "entry_basis": "START_EXHIBITION_PROVISIONAL_NOT_ACTUAL",
        "modes": {"national_only": {
            "top10_boat_research_only": [
                "1-2-3", "1-2-4", "1-2-5", "1-2-6", "1-3-2",
                "1-3-4", "1-3-5", "1-3-6", "1-4-2", "1-4-3",
            ]
        }},
    }
    return report, candidate


class V318ShadowFreeze(unittest.TestCase):
    def test_immutable_digest_and_unverified_flags(self):
        report, candidate = inputs()
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            t = datetime(2026, 10, 13, 16, 20, tzinfo=JST)
            first = freeze_file(root, report, candidate, t)
            self.assertTrue((root / first["path"]).is_file())
            self.assertEqual(len(first["sha256"]), 64)
            self.assertFalse(first["record"]["results_read"])
            self.assertFalse(first["record"]["formal_fresh_read"])
            self.assertFalse(first["record"]["model_promotion_authorized"])
            self.assertFalse(first["record"]["wagers_authorized"])
            self.assertFalse(first["record"]["independent_actual_entry_verified"])
            with self.assertRaises(ValueError):
                freeze_file(root, report, candidate, t)

    def test_late_and_incomplete_bundle_rejected(self):
        report, candidate = inputs()
        with self.assertRaises(ValueError):
            build_freeze(report, candidate, datetime(2026, 10, 13, 16, 41, tzinfo=JST))
        report["ready_for_research_review"] = False
        with self.assertRaises(ValueError):
            build_freeze(report, candidate, datetime(2026, 10, 13, 16, 20, tzinfo=JST))

    def test_bad_tickets_and_promotion_flags_rejected(self):
        report, candidate = inputs()
        candidate["modes"]["national_only"]["top10_boat_research_only"][0] = "1-1-2"
        with self.assertRaises(ValueError):
            build_freeze(report, candidate, datetime(2026, 10, 13, 16, 20, tzinfo=JST))
        report, candidate = inputs()
        candidate["production_eligible"] = True
        with self.assertRaises(ValueError):
            build_freeze(report, candidate, datetime(2026, 10, 13, 16, 20, tzinfo=JST))
        report, candidate = inputs()
        candidate["race_key"] = "20261013-22-11"
        with self.assertRaises(ValueError):
            build_freeze(report, candidate, datetime(2026, 10, 13, 16, 20, tzinfo=JST))


if __name__ == "__main__":
    unittest.main()
