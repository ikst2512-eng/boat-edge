"""V253 no-network tests: exact freeze/result boundary and staged evidence."""
import copy
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import unittest

from scripts.boat_edge_v253_miss_audit import (build, category, validate_entry,
    verified_site_rows, V236_V1, V236_V2, V236_V3)

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
        self.assertLessEqual(result["lanes"]["v236"]["races_verified"],result["site_verified_reference_races"])
        self.assertLessEqual(result["lanes"]["v240"]["races_verified"],result["site_verified_reference_races"])

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
                self.assertEqual(row["categories"]["hit10"],"second_absent_given_head")
            self.assertEqual(build(root)["lanes"]["v236"]["races_verified"],1)
        finally:tmp.cleanup()

    def make_future_5mode(self,root,policy):
        """Synthetic policy on existing verified SITE-only frozen/source fixture."""
        f=root/f"data/site_autopilot/v236_frozen/{KEY}.json"
        p=root/f"data/site_autopilot/v236_scored/{KEY}.json"
        frozen=json.loads(f.read_text(encoding="utf-8"))
        scored=json.loads(p.read_text(encoding="utf-8"))
        hit=frozen["comparators"]["hit10"]
        win=scored["official_result"]
        self.assertNotIn(win,hit)
        candidate=hit[:2]+[win]+hit[2:9]
        self.assertEqual(len(set(candidate)),10)
        frozen["comparison_policy"]=policy
        frozen["comparators"]["headsecond10"]=candidate
        f.write_text(json.dumps(frozen,sort_keys=True),encoding="utf-8")
        scored["frozen_candidate_sha256"]=hashlib.sha256(f.read_bytes()).hexdigest()
        scored["candidate_policy"]=policy
        scored["outcomes"]["headsecond10"]=True
        scored["ticket_counts"]["headsecond10"]=10
        scored["prefix_outcomes"]={
            mode:{str(k):win in frozen["comparators"][mode][:k] for k in (3,5,10)}
            for mode in ("hit10","headsecond10")}
        p.write_text(json.dumps(scored,sort_keys=True),encoding="utf-8")
        return f,p

    def test_prospective_v2_and_v3_misses_are_counted_only_in_own_policy(self):
        for policy,other in ((V236_V2,V236_V3),(V236_V3,V236_V2)):
            with self.subTest(policy=policy):
                tmp,root=self.fixture()
                try:
                    self.make_future_5mode(root,policy)
                    site=verified_site_rows(root)[KEY]
                    record=validate_entry(root,"v236",KEY,site)
                    self.assertIsNotNone(record)
                    self.assertEqual(record["categories"]["hit10"],"second_absent_given_head")
                    self.assertEqual(record["categories"]["headsecond10"],"hit")
                    output=build(root)
                    baseline=output["lanes"]["v236"]
                    self.assertEqual(baseline["races_verified"],1)
                    self.assertEqual(baseline["miss_categories"]["hit10"]["second_absent_given_head"],1)
                    self.assertEqual(baseline["headsecond_by_frozen_policy"][policy]["matched_races"],1)
                    self.assertEqual(baseline["headsecond_by_frozen_policy"][policy]["miss_categories"]["headsecond10"]["hit"],1)
                    self.assertEqual(baseline["headsecond_by_frozen_policy"][other]["matched_races"],0)
                    self.assertEqual(output["lanes"]["v240"]["races_verified"],1)
                finally:tmp.cleanup()

    def test_malformed_future_headsecond_prefix_and_policy_not_scored(self):
        for bad in ("policy","prefix","missing_candidates"):
            with self.subTest(bad=bad):
                tmp,root=self.fixture()
                try:
                    f,p=self.make_future_5mode(root,V236_V3)
                    data=json.loads(p.read_text(encoding="utf-8"))
                    if bad=="policy":data["candidate_policy"]=V236_V2
                    elif bad=="prefix":data["prefix_outcomes"]["headsecond10"]["3"]=False
                    else:
                        src=json.loads(f.read_text(encoding="utf-8"))
                        del src["comparators"]["headsecond10"]
                        f.write_text(json.dumps(src,sort_keys=True))
                        data["frozen_candidate_sha256"]=hashlib.sha256(f.read_bytes()).hexdigest()
                    p.write_text(json.dumps(data,sort_keys=True),encoding="utf-8")
                    result=build(root)
                    self.assertEqual(result["lanes"]["v236"]["races_verified"],0)
                    self.assertEqual(result["lanes"]["v240"]["races_verified"],1)
                finally:tmp.cleanup()

    def test_missing_formal_cohort_races_never_passes_read_guard(self):
        tmp,root=self.fixture()
        try:
            p=root/"data/formal_status.json"
            d=json.loads(p.read_text(encoding="utf-8"))
            del d["formalFirst100"]["races"]
            p.write_text(json.dumps(d),encoding="utf-8")
            with self.assertRaisesRegex(AssertionError,"FORMAL_COHORT_ACTIVE"):
                build(root)
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
