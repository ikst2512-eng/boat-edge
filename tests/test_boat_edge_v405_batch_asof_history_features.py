"""V405 fixture-only indexed-batch parity to V404 single-snapshot oracle."""
import csv
import hashlib
import io
import json
import random
import sys
import unittest
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from boat_edge_v400_five_year_history_research import COLUMNS, JST
from boat_edge_v404_asof_history_features import snapshot
from boat_edge_v405_batch_asof_history_features import build_batch, MODEL


def mk_key(day, venue, race):
    return day.strftime("%Y%m%d") + f"{venue:02d}{race:02d}"


def fake_race(day, venue, race, publish_hour=19, delay_days=0,
              racers=(4501,4502,4503,4504,4505,4506)):
    publish = datetime.combine(day+timedelta(days=delay_days),
                               datetime.min.time(), JST) + timedelta(hours=publish_hour)
    key = mk_key(day,venue,race)
    return [{
        "race_key":key, "boat":str(i), "racer_id":str(racers[i-1]),
        "actual_course":str(7-i), "finish":str((i % 6)+1),
        "published_at":publish.isoformat(),
    } for i in range(1,7)]


def csv_data(rows):
    out=io.StringIO(newline="")
    w=csv.DictWriter(out,fieldnames=COLUMNS,lineterminator="\n")
    w.writeheader()
    w.writerows(sorted(rows,key=lambda x:(x["race_key"],int(x["boat"]))))
    raw=out.getvalue().encode()
    return raw, {
        "schema":"BOAT_EDGE_V400_STAGED_HISTORY_MANIFEST_V1",
        "csv_sha256":hashlib.sha256(raw).hexdigest(),
        "source_name":"SYNTHETIC_ONLY","source_locator":"fixture:none",
        "rights_evidence":"synthetic fixtures are author-created",
        "rights_review_status":"OPERATOR_REVIEWED_OFFLINE_RESEARCH_ONLY",
        "normalization_protocol":"fixture-v405",
    }


def b_target(day, venue=1,race=1, hour=8):
    return {"schema":"BOAT_EDGE_V404_B_ONLY_TARGET_ROSTER_V1",
            "race_key":mk_key(day,venue,race),
            "deadline_jst":(datetime.combine(day,datetime.min.time(),JST)
                            +timedelta(hours=hour,minutes=35)).isoformat(),
            "entries":[{"boat":i,"racer_id":str(4500+i)} for i in range(1,7)]}


class V405IndexedBatchTests(unittest.TestCase):
    def setUp(self):
        rng=random.Random(14042026)
        day=date(2022,1,1)
        rows=[]
        for i in range(130):
            d=day+timedelta(days=i*13)
            v=(i%24)+1
            r=(i%12)+1
            delay=2 if i%17==0 else 0
            rows+=fake_race(d,v,r,
                            publish_hour=(3 if i%11==0 else 19),
                            delay_days=delay)
        # After-target event whose published_at is after target close.
        rows+=fake_race(date(2026,9,30),1,1,publish_hour=19)
        # Same-date earlier race that was already published at 7am.
        rows+=fake_race(date(2026,9,30),1,2,publish_hour=7)
        # Delayed previous-day result published after today's 8:35 deadline.
        rows+=fake_race(date(2026,9,29),1,3,publish_hour=10,delay_days=1)
        self.raw,self.manifest=csv_data(rows)
        self.targets=[
            b_target(date(2026,9,30),1,1),
            b_target(date(2026,9,30),1,2),
            b_target(date(2026,9,30),1,4),
            b_target(date(2024,6,1),3,2),
            b_target(date(2022,1,1),1,1),
            b_target(date(2023,10,1),5,5),
            b_target(date(2025,10,1),20,12),
            b_target(date(2026,5,20),7,3),
            b_target(date(2021,10,1),2,2),
            b_target(date(2026,9,30),1,6,hour=23),
        ]

    def assert_parity(self,targets):
        actual=build_batch(self.raw,self.manifest,targets)
        self.assertEqual(actual["schema"],MODEL)
        self.assertFalse(actual["accuracy_improvement_proven"])
        self.assertFalse(actual["timestamps_and_rights_independently_verified"])
        for t,out in zip(targets, actual["snapshots"]):
            self.assertEqual(out,snapshot(self.raw,self.manifest,t),
                             "V405 not byte-logically equivalent to V404 for "+t["race_key"])
        return actual

    def test_all_targets_exact_v404_parity(self):
        r=self.assert_parity(self.targets)
        self.assertEqual(r["target_count"],len(self.targets))
        self.assertEqual(r["history_race_count"],133)

    def test_reverse_target_order_preserves_each_snapshot(self):
        a=self.assert_parity(self.targets)
        b=self.assert_parity(list(reversed(self.targets)))
        self.assertEqual(a["snapshots"],list(reversed(b["snapshots"])))

    def test_same_day_target_yesterday_and_same_target_protection(self):
        result=self.assert_parity(self.targets)
        first=result["snapshots"][0]
        self.assertEqual(first["same_target_outcome_excluded"],1)
        self.assertGreater(first["historical_races_not_yet_available"],0)
        self.assertFalse(first["target_b_roster_historic_predeadline_capture_verified"])

    def test_next_day_results_not_predeadline(self):
        self.assert_parity([b_target(date(2026,9,30),1,4,hour=8)])

    def test_late_target_on_same_day(self):
        r=self.assert_parity([b_target(date(2026,9,30),1,4,hour=23)])
        self.assertGreater(r["snapshots"][0]["historical_races_eligible_before_target"],0)

    def test_day_boundary_90_365_1095_1826(self):
        self.assert_parity([
            b_target(date(2024,4,1),1,1),
            b_target(date(2025,1,1),1,1),
            b_target(date(2026,1,1),1,1),
            b_target(date(2026,9,30),1,4),
        ])


    def test_explicit_calendar_window_boundaries_parity(self):
        end = date(2026,9,30)
        ages = (0, 89, 90, 364, 365, 1094, 1095, 1825)
        rows = []
        for age in ages:
            d = end - timedelta(days=age)
            rows += fake_race(d,1,1,publish_hour=(7 if age==0 else 19))
        raw, man = csv_data(rows)
        target = b_target(end,2,2,hour=8)
        batched = build_batch(raw,man,[target])["snapshots"][0]
        single = snapshot(raw,man,target)
        self.assertEqual(batched,single)
        actual = batched["national_actual_course_counts"]["1"]
        self.assertEqual(
            [actual[str(w)]["entries"] for w in (90,365,1095,1826)],
            [2,4,6,8])

    def test_empty_history_has_empty_snapshots(self):
        raw,man=csv_data([])
        targets=[b_target(date(2026,9,30))]
        a=build_batch(raw,man,targets)
        self.assertEqual(a["snapshots"][0],snapshot(raw,man,targets[0]))

    def test_empty_targets_accepted_without_results(self):
        r=build_batch(self.raw,self.manifest,[])
        self.assertEqual(r["target_count"],0)
        self.assertEqual(r["snapshots"],[])

    def test_many_targets_parity_randomized(self):
        rng=random.Random(4095)
        days=[date(2022,1,1)+timedelta(days=rng.randrange(1720))
              for _ in range(50)]
        targets=[]
        for i,d in enumerate(days):
            targets.append(b_target(d,venue=i%24+1,
                                    race=i%12+1,hour=8+(i%14)))
        self.assert_parity(targets)

    def test_duplicate_target_rejected(self):
        t=self.targets[0]
        with self.assertRaisesRegex(ValueError,"DUPLICATE_B_ONLY_TARGET_RACE_KEY"):
            build_batch(self.raw,self.manifest,[t,t])

    def test_protected_target_rejected(self):
        with self.assertRaisesRegex(ValueError,"PROTECTED_OR_UNSUPPORTED_TARGET_DATE"):
            build_batch(self.raw,self.manifest,[b_target(date(2026,10,1))])

    def test_outcome_in_target_rejected(self):
        t=b_target(date(2026,9,30))
        t["entries"][0]["finish"]=1
        with self.assertRaisesRegex(ValueError,"TARGET_MUST_NOT_CONTAIN_OUTCOME_OR_ACTUAL_COURSE"):
            build_batch(self.raw,self.manifest,[t])

    def test_source_sha_tamper_rejected(self):
        bad=dict(self.manifest,csv_sha256="a"*64)
        with self.assertRaisesRegex(ValueError,"RAW_HISTORY_SHA256_MISMATCH"):
            build_batch(self.raw,bad,self.targets)

    def test_impossible_published_before_own_race_rejected(self):
        # A fake K record claiming availability the day before its own race
        # must never enter the as-of sweep even if a target is later.
        bad = fake_race(date(2026, 9, 29), 1, 1)
        for row in bad:
            row["published_at"] = "2026-09-28T21:00:00+09:00"
        src, man = csv_data(bad)
        with self.assertRaisesRegex(ValueError, "HISTORICAL_PUBLISHED_AT_LEAK"):
            build_batch(src, man, [b_target(date(2026, 9, 30), 2, 2)])

    def test_protected_history_rejected(self):
        src,man=csv_data(fake_race(date(2026,10,1),1,1))
        with self.assertRaisesRegex(ValueError,"RACE_OUTSIDE_ALLOWED_RANGE"):
            build_batch(src,man,self.targets)

    def test_non_six_course_history_rejected(self):
        bad=fake_race(date(2026,9,1),1,1)
        bad[1]["actual_course"]=bad[0]["actual_course"]
        src,man=csv_data(bad)
        with self.assertRaisesRegex(ValueError,"ACTUAL_COURSE_NOT_SIX_WAY"):
            build_batch(src,man,self.targets)

    def test_source_order_independent_via_sorted_csv(self):
        self.assert_parity(self.targets)

    def test_batch_idempotence(self):
        r1=build_batch(self.raw,self.manifest,self.targets)
        r2=build_batch(self.raw,self.manifest,self.targets)
        self.assertEqual(json.dumps(r1,sort_keys=True),
                         json.dumps(r2,sort_keys=True))

    def test_no_target_actual_course_or_model_promotion(self):
        r=self.assert_parity(self.targets)
        for s in r["snapshots"]:
            self.assertTrue(s["actual_course_of_target_not_observed_or_inferred"])
            self.assertFalse(s["model_promotion_authorized"])
            self.assertFalse(s["formal_fresh_read"])

    def test_target_list_limit_fails_closed(self):
        with self.assertRaisesRegex(ValueError,"TARGET_LIST_REQUIRED_OR_TOO_LARGE"):
            build_batch(self.raw,self.manifest,[self.targets[0]]*20001)


if __name__=="__main__":
    unittest.main()
