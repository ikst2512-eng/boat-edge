import unittest
from scripts.boat_edge_v303_ranked_topk_gate import inspect

TOP = ["1-2-3", "1-2-4", "1-3-2", "1-3-4", "1-4-2",
       "1-4-3", "2-1-3", "2-1-4", "2-3-1", "2-3-4"]

def fixture():
    return {"scope": "SITE_REFERENCE_UNSEEN_PRE_RESULT_ONLY_NOT_FORMAL_FRESH",
            "formal_results_seen": False, "formal_gate_unlocked": False,
            "top10": TOP[:],
            "frozen_mode_tickets": {"hit": [{"combo": x} for x in TOP]}}

class TopKReadinessTests(unittest.TestCase):
    def test_ready(self):
        self.assertEqual(inspect(fixture()), "RANKED_TOP3_TOP5_TOP10_AVAILABLE")

    def test_reordered_rank_rejected(self):
        item = fixture()
        item["frozen_mode_tickets"]["hit"].reverse()
        self.assertEqual(inspect(item), "RANKED_HIT_TOP10_MISMATCH")

    def test_duplicate_rejected(self):
        item = fixture()
        item["top10"][1] = item["top10"][0]
        self.assertEqual(inspect(item), "TOP10_INVALID")

    def test_formal_guard(self):
        item = fixture()
        item["formal_results_seen"] = True
        self.assertEqual(inspect(item), "FORMAL_GATE_UNVERIFIED")

    def test_invalid_combo(self):
        item = fixture()
        item["top10"][0] = "1-1-3"
        self.assertEqual(inspect(item), "COMBO_INVALID")
