"""V304 fixture-only V254 model identity gate regression; NO outcome access."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from scripts import boat_edge_v254_third_tail as m

KEY = "20261013-14-11"
HIT = ["1-2-3","1-3-2","1-2-4","1-4-2","1-3-4",
       "2-1-3","2-3-1","3-1-2","4-1-2","5-1-2"]
HOLE = HIT + ["1-2-5","2-1-4"]


class V304SourceModelIdentity(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        formal = self.root / "data/formal_status.json"
        formal.parent.mkdir(parents=True)
        formal.write_text(json.dumps({"guards": {"results_seen": False, "unlock": False,
                            "scoring": False, "RESULT_UNLOCK_TOKEN": None},
                            "formalFirst100": {"races": 0}}), encoding="utf-8")
        self.path = self.root / "data/site_autopilot/v232_cohort" / (KEY + ".json")
        self.path.parent.mkdir(parents=True)
        self.now = m.stamp("2026-10-13T05:51:00+00:00")
        self.source = {
            "schema":"BOAT_EDGE_V232_SITE_PROSPECTIVE_ACCURACY_COHORT_V1",
            "scope":"SITE_REFERENCE_UNSEEN_PRE_RESULT_ONLY_NOT_FORMAL_FRESH",
            "race_key":KEY,"model_id":"SITE_REFERENCE_V122",
            "deadline_jst":"2026-10-13T15:00:00+09:00",
            "snapshot_saved_at":"2026-10-13T05:40:00+00:00",
            "evidence_committed_at":"2026-10-13T05:45:00+00:00",
            "formal_results_seen":False,"formal_gate_unlocked":False,
            "paper_purchases_authorized":False,"real_purchases_authorized":False,
            "production_accuracy_claim":False,
            "top10":HIT,
            "frozen_mode_tickets":{"hit":[{"combo":c} for c in HIT],
                                   "hole":[{"combo":c} for c in HOLE]},
        }

    def row(self, model_id):
        item=dict(self.source)
        if model_id is None:
            item.pop("model_id")
        else:
            item["model_id"]=model_id
        self.path.write_text(json.dumps(item)+"\n",encoding="utf-8")
        return item

    def first(self, root, path):
        self.assertEqual(path,self.path)
        return {"commit":"a"*40, "at":m.stamp("2026-10-13T05:46:00+00:00"),
                "sha256":m.sha(path)}

    def test_only_existing_v122_model_accepted(self):
        self.row("SITE_REFERENCE_V122")
        with patch.object(m,"git_first",side_effect=self.first):
            prepared,error=m.make_pre(self.root,self.path,self.now)
        self.assertIsNone(error,error)
        self.assertEqual(prepared["comparators"]["hit10"], HIT)
        self.assertEqual(len(prepared["comparators"]["third_tail10"]),10)
        self.assertFalse(prepared["results_seen_at_freeze"])
        self.assertFalse(prepared["production_model_changed"])
        self.assertFalse(prepared["model_promotion_authorized"])

    def test_unverified_other_model_never_reaches_future_freeze(self):
        for value in ("SITE_REFERENCE_V123","CURRENT_FORMAL", "unknown", "", None):
            with self.subTest(value=value):
                self.row(value)
                with patch.object(m,"git_first",side_effect=self.first), patch.object(m,"get",wraps=m.get) as reads:
                    prepared,error=m.make_pre(self.root,self.path,self.now)
                self.assertIsNone(prepared)
                self.assertEqual(error,"SOURCE_FRESH_CONTRACT_NOT_MET")
                self.assertFalse(any("results" in str(c.args[0]) or "payout" in str(c.args[0])
                                     for c in reads.call_args_list))

    def test_refuses_mixed_model_without_writing_any_future_candidate(self):
        self.row("SITE_REFERENCE_V999")
        with patch.object(m,"git_first",side_effect=self.first):
            output=m.freeze(self.root,self.now)
        self.assertEqual(output["new_frozen_this_run"],0)
        self.assertEqual(output["rejected_current_run"]["SOURCE_FRESH_CONTRACT_NOT_MET"],1)
        self.assertFalse((self.root/"data/site_autopilot/v254_frozen"/(KEY+".json")).exists())

    def test_formal_fresh_lock_still_precedes_parent_read(self):
        self.row("SITE_REFERENCE_V122")
        formal=self.root/"data/formal_status.json"
        bad=json.loads(formal.read_text())
        bad["formalFirst100"]["races"]=1
        formal.write_text(json.dumps(bad),encoding="utf-8")
        with patch.object(m,"get",wraps=m.get) as reads:
            with self.assertRaisesRegex(RuntimeError,"FORMAL_COHORT"):
                m.make_pre(self.root,self.path,self.now)
        self.assertEqual([c.args[0] for c in reads.call_args_list],[formal])


if __name__ == "__main__":
    unittest.main()
