"""V392 card-only, no-network prospective fixture regressions."""
from __future__ import annotations
from datetime import datetime, timedelta
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from scripts import boat_edge_v392_card_preview as m

KEY = "20261015-14-01"
NOW = datetime(2026, 10, 14, 20, 0, tzinfo=m.JST)


def card(key=KEY, fetched=None):
    fetched = fetched or NOW
    return {
        "race_key": key, "meta": {
            "date": f"{key[:4]}-{key[4:6]}-{key[6:8]}",
            "venue_code": key[9:11], "venue": "鳴門",
            "race_no": int(key[-2:]), "deadline": "08:35",
            "phase": "PRE_RESULT", "results_seen": False,
            "unlock": False, "scoring": False,
        },
        "source_audit": {"race_card": {
            "status": "ok", "fetched_at": fetched.isoformat(), "sha256": "a"*64}},
        "racers": [{
            "lane": i, "registration_no": str(5000+i), "name": "選手",
            "class": "A1" if i == 1 else "B1", "avg_st": 0.14 + i/100,
            "national": {"win_rate": 7.8-i*.5},
            "local": {"win_rate": 5.0},
            "motor": {"quinella_rate": 30+i}, "raw_text": str(i),
        } for i in range(1, 7)]
    }


def save(root, path, obj):
    p = root/path
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, ensure_ascii=False), encoding="utf-8")
    return p


class FakeResponse:
    status_code = 200
    apparent_encoding = "utf-8"
    encoding = "utf-8"
    def __init__(self, url, content):
        self.url = url
        self.content = content.encode("utf-8")
        self.text = content


def racelist_html():
    clocks = ["08:35", "09:01", "09:27", "09:53", "10:21", "10:52",
              "11:20", "11:49", "12:18", "12:47", "13:16", "13:45"]
    head = "<tr><td>締切予定時刻 " + " ".join(clocks) + "</td></tr>"
    rows = "".join(
        "<tr><td>" + str(i) + " " + str(5000+i) +
        " / A1 <a>選手</a> 山口/山口 27歳/52.0kg F0 L0 0.17 "
        "6.49 44.95 67.89 0.00 0.00 0.00 54 33.67 50.00 28 38.38 50.51"
        "</td></tr>" for i in range(1, 7)
    )
    return "<html><title>出走表</title><table>"+head+rows+"</table></html>"


class FakeSession:
    def get(self, url, timeout, allow_redirects):
        if allow_redirects:
            raise AssertionError("REDIRECTS_FORBIDDEN")
        if "race/index?" in url:
            html = ('<a href="/owpc/pc/race/racelist?hd=20261015&jcd=14&rno=1">'
                    '鳴門</a>')
        elif "race/racelist?" in url:
            html = racelist_html()
        else:
            raise AssertionError("NON_RACELIST_ENDPOINT_" + url)
        return FakeResponse(url, html)


class V392Tests(unittest.TestCase):
    def test_full_120_ranks_and_top_prefixes_without_odds_or_result(self):
        d = card()
        p = m.make_preview(d, NOW)
        self.assertEqual(p["schema"], m.SCHEMA)
        self.assertEqual(p["model_id"], m.MODEL)
        self.assertEqual(p["prediction_kind"], "EARLY_CARD_ONLY_REFERENCE_NOT_FINAL")
        self.assertEqual(len(p["ranked_120"]), 120)
        self.assertEqual(len({x["combo"] for x in p["ranked_120"]}), 120)
        self.assertEqual([x["rank"] for x in p["ranked_120"]], list(range(1, 121)))
        self.assertEqual(p["top3"], p["top10"][:3])
        self.assertEqual(p["top5"], p["top10"][:5])
        self.assertEqual(p["head_candidate"], int(p["top10"][0][0]))
        self.assertEqual(p["racer_inputs_by_lane"][0][1], "5001")
        self.assertFalse(p["score_is_calibrated_probability"])
        self.assertFalse(p["odds_used"])
        self.assertIsNone(p["stake_yen"])
        self.assertFalse(p["guards"]["results_seen"])
        self.assertFalse(p["formal_fresh_claim"])

    def test_refuse_missing_or_scratch_or_mismatched_inputs(self):
        d = card()
        self.assertFalse(m.usable_card(dict(d, racers=d["racers"][:5]), NOW))
        d["racers"][1]["registration_no"] = "5001"
        self.assertFalse(m.usable_card(d, NOW))
        d = card()
        d["racers"][2]["status"] = "出走取消"
        self.assertIsNone(m.make_preview(d, NOW))
        d = card()
        d["source_audit"]["race_card"]["status"] = "unverified"
        self.assertIsNone(m.make_preview(d, NOW))
        d = card()
        d["meta"]["unlock"] = True
        self.assertIsNone(m.make_preview(d, NOW))
        d = card()
        d["meta"]["venue_code"] = "18"
        self.assertIsNone(m.make_preview(d, NOW))
        d = card()
        self.assertIsNone(m.make_preview(d, datetime(2026,10,15,8,35,tzinfo=m.JST)))
        d = card(fetched=datetime(2026,10,15,8,36,tzinfo=m.JST))
        self.assertIsNone(m.make_preview(d, NOW))

    def test_missing_numbers_not_made_up_and_unchanged_card_not_rewritten(self):
        with tempfile.TemporaryDirectory() as base:
            root=Path(base)
            d=card()
            d["racers"][0]["avg_st"] = None
            d["racers"][1]["local"]["win_rate"] = None
            p=m.make_preview(d,NOW)
            self.assertIn("avg_st",p["missing_card_fields"])
            self.assertIn("local.win_rate",p["missing_card_fields"])
            self.assertTrue(m.save_preview(root,d,NOW))
            path=root/"data/site_early_previews"/(KEY+".json")
            blob=path.read_bytes()
            d["source_audit"]["race_card"]["sha256"] = "b"*64
            self.assertFalse(m.save_preview(root,d,NOW+timedelta(minutes=1)))
            self.assertEqual(path.read_bytes(),blob)

    def test_today_only_reads_selected_future_source_cards(self):
        with tempfile.TemporaryDirectory() as base:
            root=Path(base)
            key="20261014-14-01"
            d=card(key,fetched=datetime(2026,10,14,7,0,tzinfo=m.JST))
            save(root,"data/today.json",{"date":"2026-10-14","venues":[{
                "jcd":"14","races":[{"race_key":key,"deadline":"08:35"}]}]})
            save(root,"data/races/"+key+".json",d)
            at=datetime(2026,10,14,7,1,tzinfo=m.JST)
            state=m.build_today(root,at)
            self.assertEqual(state,{"candidates":1,"updated":1})
            self.assertEqual(m.build_today(root,at),{"candidates":1,"updated":0})
            self.assertEqual(m.build_today(root,at.replace(hour=9)),{"candidates":0,"updated":0})

    def test_official_next_day_index_and_all_12_cards(self):
        with tempfile.TemporaryDirectory() as base:
            root=Path(base)
            with patch.object(m,"jstnow",return_value=NOW+timedelta(minutes=1)):
                status=m.collect_tomorrow(root,NOW,FakeSession())
            self.assertEqual(status["status"],"VERIFIED_CARD_PREVIEWS")
            self.assertEqual(status["cards"],12)
            idx=m.get_json(root/"data/site_early_calendar/index.json")
            self.assertEqual(idx["dates"],["20261015"])
            calendar=m.get_json(root/"data/site_early_calendar/20261015.json")
            self.assertEqual(len(calendar["venues"][0]["races"]),12)
            self.assertEqual(calendar["venues"][0]["races"][0]["file"],
                             "data/early_races/20261015-14-01.json")
            d=m.get_json(root/"data/early_races"/(KEY+".json"))
            self.assertTrue(m.usable_card(d,NOW+timedelta(minutes=1)))
            p=m.get_json(root/"data/site_early_previews"/(KEY+".json"))
            self.assertEqual(len(p["ranked_120"]),120)
            self.assertFalse((root/"data/races"/(KEY+".json")).exists())

    def test_no_future_network_outside_nightly_window(self):
        with tempfile.TemporaryDirectory() as base:
            out=m.collect_tomorrow(Path(base),NOW.replace(hour=8),FakeSession())
            self.assertEqual(out["status"],"OUTSIDE_NIGHTLY_COLLECTION_WINDOW")

    def test_formal_gate_is_closed_before_any_publishing(self):
        with tempfile.TemporaryDirectory() as base:
            root=Path(base)
            save(root,"data/formal_status.json",{"guards":{
                "results_seen":False,"unlock":False,"scoring":False,"RESULT_UNLOCK_TOKEN":None}})
            m.formal_closed(root)
            save(root,"data/formal_status.json",{"guards":{
                "results_seen":False,"unlock":True,"scoring":False,"RESULT_UNLOCK_TOKEN":None}})
            with self.assertRaisesRegex(RuntimeError,"FORMAL_GUARDS"):
                m.formal_closed(root)


if __name__ == "__main__":
    unittest.main()
