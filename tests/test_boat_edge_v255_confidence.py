"""V255 real-Git forward-only calibration honesty and deterministic source tests."""
import json
from pathlib import Path
import tempfile
import unittest

from scripts.boat_edge_v255_confidence_audit import (
    build, inspect, site_rows, wilson, formal_guard
)

ROOT=Path(__file__).resolve().parents[1]


class ConfidenceHonesty(unittest.TestCase):
    def test_empirical_site_only_denominator_is_recomputed(self):
        report=build(ROOT)
        n=report["prospective_source_verified_races"]
        self.assertGreater(n,0)
        self.assertLessEqual(n,report["site_settled_reference_races"])
        self.assertEqual(n,len(report["rows"]))
        self.assertEqual(sum(x["top10_hit"] for x in report["rows"]),report["top10"]["hits"])
        self.assertEqual(sum(x["head_hit"] for x in report["rows"]),report["head"]["hits"])
        self.assertEqual(report["head"]["wilson_95_percent"],wilson(report["head"]["hits"],n))
        self.assertFalse(report["formal_result_access"])
        self.assertFalse(report["accuracy_improvement_proven"])
        self.assertFalse(report["production_model_changed"])
        self.assertEqual(report["real_or_paper_wagers_placed"],0)

    def test_top10_normalized_relative_score_not_calibrated(self):
        v=build(ROOT)
        w=v["hit10_frozen_relative_weight"]
        self.assertEqual(w["verified_races"],v["prospective_source_verified_races"])
        self.assertEqual(w["normalized_to_100_in_races"],
                         sum(x["relative_weight_normalized_near_100"] for x in v["rows"]))
        self.assertIn("NOT_120_OUTCOME_PROBABILITY",w["interpretation"])
        self.assertTrue(all(0 <= x["relative_weight_max"] <= 100 for x in v["rows"]))
        self.assertTrue(all(0 <= x["relative_weight_min"] <= x["relative_weight_max"] for x in v["rows"]))

    def test_head_is_different_from_top10_ticket_hit(self):
        v=build(ROOT)
        # Independently calculated fields; don't present a single 90% internal score
        # as the empirical rate for either of these two outcomes.
        self.assertEqual(v["top10"]["races"],v["head"]["races"])
        self.assertTrue(all(type(x["head_hit"]) is bool for x in v["rows"]))
        self.assertTrue(all(type(x["top10_hit"]) is bool for x in v["rows"]))

    def test_tampering_rejects_record_not_backfills(self):
        rows=site_rows(ROOT)
        key=next(iter(rows))
        r=dict(rows[key])
        self.assertIsNotNone(inspect(ROOT,key,r))
        r["precommitted_sha256"]="f"*64 if r["precommitted_sha256"]!="f"*64 else "0"*64
        self.assertIsNone(inspect(ROOT,key,r))
        r=dict(rows[key]);r["head_hit"]=not r["head_hit"]
        self.assertIsNone(inspect(ROOT,key,r))
        r=dict(rows[key]);r["first_frozen_commit"]="0"*40
        self.assertIsNone(inspect(ROOT,key,r))

    def test_wilson_interval_sensible_and_empty_is_missing(self):
        self.assertIsNone(wilson(0,0))
        a=wilson(0,1);b=wilson(1,1);c=wilson(2,8)
        self.assertTrue(0<=a[0]<=a[1]<100)
        self.assertTrue(0<b[0]<=b[1]<=100)
        self.assertTrue(c[0]<25<c[1])

    def test_formal_unlock_aborts_every_source_read(self):
        with tempfile.TemporaryDirectory() as p:
            root=Path(p);dest=root/"data/formal_status.json";dest.parent.mkdir(parents=True)
            dest.write_text(json.dumps({"guards":{
                "results_seen":True,"unlock":False,"scoring":False,"RESULT_UNLOCK_TOKEN":None}}))
            with self.assertRaises(AssertionError):formal_guard(root)

    def test_no_calibrated_90_percent_ui_claim(self):
        src=(ROOT/"assets/boat_edge_v108.js").read_text()
        self.assertIn("内部スコア（未校正）",src)
        self.assertNotIn("<small>内部信頼度</small><strong>${conf}%</strong>",src)
        self.assertIn("的中確率ではありません",src)
        self.assertIn("be255-score-note",src)


if __name__=="__main__":
    unittest.main()
