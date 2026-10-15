"""Only synthetic pre-scored rows. Never reads results or Formal Fresh."""
import importlib.util
import unittest
from datetime import date,timedelta
from pathlib import Path

SRC=Path(__file__).resolve().parent.parent/"scripts/boat_edge_02_paired_topk_evidence.py"
spec=importlib.util.spec_from_file_location("paired_evidence",SRC)
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

def fake_data(candidate_wins=True):
    manifest={"schema":mod.SCHEMA,"stage":"2025_HISTORICAL_REPLAY_NOT_PROSPECTIVE",
        "licence_archive_reviewed":True,"external_scoring_reviewed":True,
        "archive_receipt_sha256":"a"*64,"scoring_receipt_sha256":"b"*64,
        "baseline_model_sha256":"c"*64,"candidate_model_sha256":"d"*64,
        "paired_rows":[]}
    for i in range(600):
        day=date(2025,1,1)+timedelta(days=i//12)
        key=f"{day.strftime('%Y%m%d')}-{(i%24)+1:02d}-{(i%12)+1:02d}"
        baseline={"3":False,"5":False,"10":False}
        candidate={"3":candidate_wins,"5":candidate_wins,"10":candidate_wins}
        manifest["paired_rows"].append({"race_key":key,
            "same_race_same_ten_ticket_budget":True,
            "independent_input_cutoff_checked":True,
            "baseline_hits":baseline,"candidate_hits":candidate})
    return manifest

class PairedTopK(unittest.TestCase):
    def test_synthetic_gain_never_promotes(self):
        result=mod.compare(fake_data())
        self.assertTrue(result["research_signal_all_topk_positive"])
        self.assertFalse(result["model_promotion_authorized"])
        self.assertEqual(result["paired_races"],600)
        self.assertEqual(result["independent_dates"],50)
    def test_no_gain(self):
        self.assertFalse(mod.compare(fake_data(False))["research_signal_all_topk_positive"])
    def test_nested_hit_flags(self):
        inp=fake_data()
        inp["paired_rows"][0]["candidate_hits"]={"3":True,"5":False,"10":True}
        with self.assertRaisesRegex(ValueError,"TOPK_NESTING"):
            mod.compare(inp)
    def test_duplicate_and_no_asof(self):
        inp=fake_data()
        inp["paired_rows"].append(inp["paired_rows"][0])
        with self.assertRaisesRegex(ValueError,"DUPLICATED_RACE"):
            mod.compare(inp)
        inp=fake_data()
        inp["paired_rows"][0]["independent_input_cutoff_checked"]=False
        with self.assertRaisesRegex(ValueError,"ASOF_EVIDENCE_REQUIRED"):
            mod.compare(inp)
    def test_protected_future_and_unreviewed(self):
        inp=fake_data()
        inp["paired_rows"][0]["race_key"]="20261016-01-01"
        with self.assertRaisesRegex(ValueError,"2025_HOLDOUT"):
            mod.compare(inp)
        inp=fake_data()
        inp["licence_archive_reviewed"]=False
        with self.assertRaisesRegex(ValueError,"REVIEW_FLAGS_REQUIRED"):
            mod.compare(inp)

if __name__=="__main__":
    unittest.main()
