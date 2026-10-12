"""V320 actual SITE V232 schema fixture and safety regressions."""
import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "scripts"))
from boat_edge_v320_site_v232_baseline_adapter import baseline_from_v232


def fixture():
    tickets = ["1-3-2", "1-2-3", "1-2-5", "1-2-4", "1-5-2",
               "1-3-4", "1-4-2", "1-4-3", "1-2-6", "1-3-6"]
    return {
        "race_key": "20261012-02-09",
        "scope": "SITE_REFERENCE_UNSEEN_PRE_RESULT_ONLY_NOT_FORMAL_FRESH",
        "deadline_jst": "2026-10-12T14:48:00+09:00",
        "evidence_committed_at": "2026-10-12T05:43:56.545086+00:00",
        "formal_results_seen": False,
        "formal_gate_unlocked": False,
        "production_accuracy_claim": "NOT_PROVEN",
        "real_purchases_authorized": False,
        "model_id": "SITE_REFERENCE_V122",
        "top10": tickets,
        "top3": tickets[:3],
        "top5": tickets[:5],
        "head_top1": "1",
    }


class V320SiteBaseline(unittest.TestCase):
    def test_actual_v232_shape_converts_to_v319(self):
        result = baseline_from_v232(fixture())
        self.assertEqual(result["top10_boat"][0], "1-3-2")
        self.assertEqual(result["frozen_at_jst"], "2026-10-12T14:43:56.545086+09:00")
        self.assertTrue(result["site_timestamp_self_reported_not_git_server_attested"])
        self.assertFalse(result["source_independently_authenticated"])
        self.assertFalse(result["results_read"])
        self.assertFalse(result["formal_fresh_read"])

    def test_late_inconsistent_or_formal_unlocked_rejected(self):
        row = fixture()
        row["evidence_committed_at"] = "2026-10-12T05:49:00+00:00"
        with self.assertRaises(ValueError):
            baseline_from_v232(row)
        row = fixture()
        row["top5"][0] = "2-3-1"
        with self.assertRaises(ValueError):
            baseline_from_v232(row)
        row = fixture()
        row["formal_gate_unlocked"] = True
        with self.assertRaises(ValueError):
            baseline_from_v232(row)
        row = fixture()
        row["production_accuracy_claim"] = "PROVEN"
        with self.assertRaises(ValueError):
            baseline_from_v232(row)


if __name__ == "__main__":
    unittest.main()
