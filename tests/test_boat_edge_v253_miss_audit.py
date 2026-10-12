"""V253 no-network tests: exact freeze/result boundary and staged evidence."""
import copy
import json
from pathlib import Path
import shutil
import tempfile
import unittest

from scripts.boat_edge_v253_miss_audit import build, category, validate_entry, verified_site_rows

ROOT=Path(__file__).resolve().parents[1]
KEY="20261012-09-02"

class V253SiteOnlyMissAudit(unittest.TestCase):
    def test_ordinal_cause_categories(self):
        tickets=["1-2-3","1-3-2","2-1-4"]
        self.assertEqual(category(tickets,"1-2-3"),"hit")
        self.assertEqual(category(tickets,"3-1-2"),"head_absent")
        self.assertEqual(category(tickets,"1-4-2"),"second_absent_given_head")
        self.assertEqual(category(tickets,"1-2-4"),"third_absent_given_head_second")

    def test_current_settled_comparators_are_source_checked(self):
        result=build(ROOT)
        self.assertFalse(result["formal_result_access"])
        self.assertFalse(result["production_model_changed"])
        for lane in ("v236","v240"):
            record=result["lanes"][lane]
            self.assertGreaterEqual(record["races_verified"],1)
            for mode,counts in record["miss_categories"].items():
                self.assertEqual(sum(counts.values()),record["races_verified"])
            self.assertTrue(all(row["race_key"].startswith("20") for row in record["races"]))
        self.assertEqual(result["lanes"]["v236"]["races_verified"],8)
        self.assertEqual(result["lanes"]["v240"]["races_verified"],7)

    def fixture(self):
        tmp=tempfile.TemporaryDirectory()
        root=Path(tmp.name)
        paths=["data/formal_status.json",
          "data/site_autopilot/v241_results_current.json"]
        for lane in ("v236","v240"):
            paths.extend([f"data/site_autopilot/{lane}_frozen/{KEY}.json",
                          f"data/site_autopilot/{lane}_scored/{KEY}.json"])
        for name in paths:
            p=root/name;p.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(ROOT/name,p)
        site=root/"data/site_autopilot/v241_results_current.json"
        doc=json.loads(site.read_text(encoding="utf-8"))
        item=next(x for x in doc["rows"] if x["race_key"]==KEY)
        doc["rows"]=[item];doc["settled_verified_races"]=1
        doc["top10_hits"]=int(item["top10_hit"]);doc["head_hits"]=int(item["head_hit"])
        site.write_text(json.dumps(doc),encoding="utf-8")
        return tmp,root

    def test_one_race_pair_matches_both_scored_proofs(self):
        tmp,root=self.fixture()
        try:
            site=verified_site_rows(root)
            self.assertIn(KEY,site)
            for lane in ("v236","v240"):
                row=validate_entry(root,lane,KEY,site[KEY])
                self.assertIsNotNone(row)
                self.assertEqual(row["winning_combo"],"3-4-1")
                self.assertEqual(row["categories"]["hit10"],"head_absent")
            self.assertEqual(build(root)["lanes"]["v236"]["races_verified"],1)
        finally:tmp.cleanup()

    def test_sha_tamper_is_excluded(self):
        tmp,root=self.fixture()
        try:
            p=root/f"data/site_autopilot/v236_frozen/{KEY}.json"
            p.write_text(p.read_text().replace("1-3-4","1-5-4",1),encoding="utf-8")
            result=build(root)
            self.assertEqual(result["lanes"]["v236"]["races_verified"],0)
            self.assertEqual(result["lanes"]["v240"]["races_verified"],1)
        finally:tmp.cleanup()

    def test_late_freeze_is_excluded(self):
        tmp,root=self.fixture()
        try:
            p=root/f"data/site_autopilot/v240_frozen/{KEY}.json"
            d=json.loads(p.read_text());d["frozen_at"]="2026-10-12T12:00:00+09:00"
            p.write_text(json.dumps(d))
            result=build(root)
            self.assertEqual(result["lanes"]["v240"]["races_verified"],0)
        finally:tmp.cleanup()

    def test_bad_site_result_fails_closed(self):
        tmp,root=self.fixture()
        try:
            p=root/"data/site_autopilot/v241_results_current.json"
            d=json.loads(p.read_text());d["rows"][0]["winning_combo"]="2-4-1"
            p.write_text(json.dumps(d))
            result=build(root)
            self.assertEqual(result["lanes"]["v236"]["races_verified"],0)
            self.assertEqual(result["lanes"]["v240"]["races_verified"],0)
        finally:tmp.cleanup()

    def test_formal_results_unlock_is_rejected(self):
        tmp,root=self.fixture()
        try:
            p=root/"data/formal_status.json"
            d=json.loads(p.read_text());d["guards"]["results_seen"]=True
            p.write_text(json.dumps(d))
            with self.assertRaises(AssertionError):build(root)
        finally:tmp.cleanup()

if __name__=="__main__":unittest.main()
