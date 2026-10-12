"""V256 independent no-result/odds completeness regression tests."""
import unittest
from datetime import datetime, timezone
from scripts.boat_edge_v256_odds_guard import (
    REJECTED, is_safe_record, official_url_matches, rejected_document,
    should_replace, record_time,
)

KEY = "20261012-14-09"
URL = "https://www.boatrace.jp/owpc/pc/race/odds3t?hd=20261012&jcd=14&rno=9"
TIME = "2026-10-12T11:47:00+09:00"


def valid_document(time=TIME, count=120):
    odds={}
    for a in range(1,7):
        for b in range(1,7):
            for c in range(1,7):
                if len({a,b,c}) == 3:
                    odds[f"{a}-{b}-{c}"]=9.9
    odds=dict(list(odds.items())[:count])
    return dict(schema_version="boat-edge-site-odds-v71",
                race_key=KEY, source_url=URL,
                source="BOAT RACE オフィシャルウェブサイト 3連単オッズ",
                phase="PRE_RESULT_PURCHASE_ONLY",
                results_seen=False, scoring=False,
                fetched_at=time, available_count=len(odds),
                unavailable_count=120-len(odds),
                unavailable_combinations=[] if count == 120 else ["6-5-4"],
                odds_validation="VERIFIED", no_bet=False,
                verified_official_dom_v167=True,
                raw_official_html_sha256="a"*64,
                trifecta_odds=odds)


class V256OfficialOddsSafety(unittest.TestCase):
    def test_race_source_binding(self):
        self.assertTrue(official_url_matches(KEY,URL))
        for bad in (
            URL.replace("www.boatrace.jp","www.boatrace.jp.attacker.test"),
            URL.replace("rno=9","rno=8"),
            URL.replace("jcd=14","jcd=18"),
            URL.replace("hd=20261012","hd=20261011"),
            URL+"#fragment",
            URL+"&ignored",  # malformed flag was silently dropped by parse_qs
            URL+"&ignored=1",
            URL+"&rno=8",
            URL+"&rno=",
            URL.replace("jcd=14", "jcd=14;unexpected=1"),
        ):
            self.assertFalse(official_url_matches(KEY,bad))

    def test_only_complete_source_proven_120_is_safe(self):
        self.assertTrue(is_safe_record(valid_document(),KEY))
        self.assertFalse(is_safe_record(valid_document(count=119),KEY))
        self.assertFalse(is_safe_record(valid_document(count=60),KEY))
        altered=valid_document()
        altered["trifecta_odds"]["1-2-3"]=0
        self.assertFalse(is_safe_record(altered,KEY))
        for field in ("verified_official_dom_v167","raw_official_html_sha256"):
            altered=valid_document()
            altered.pop(field)
            self.assertFalse(is_safe_record(altered,KEY))
        altered=valid_document()
        altered["source"]="unverified"
        self.assertFalse(is_safe_record(altered,KEY))
        # float(True) and float("9.9") must not certify a 120-odds source.
        for fake_price in (True, False, "9.9", None, float("inf"), float("nan")):
            altered=valid_document()
            altered["trifecta_odds"]["1-2-3"]=fake_price
            with self.subTest(fake_price=repr(fake_price)):
                self.assertFalse(is_safe_record(altered,KEY))

    def test_rejection_always_blanks_prices_and_never_inferrs_scratch(self):
        bad=rejected_document(key=KEY,url=URL,deadline="12:19",
            checked_at="2026-10-12T11:48:00+09:00",
            error="valid_odds_too_few=60")
        self.assertEqual(bad["odds_validation"],REJECTED)
        self.assertEqual(bad["observed_numeric_count"],60)
        self.assertEqual(bad["trifecta_odds"],{})
        self.assertEqual(bad["available_count"],0)
        self.assertEqual(bad["scratch_status"],"UNVERIFIED")
        self.assertTrue(bad["no_bet"])
        self.assertTrue(is_safe_record(bad,KEY))
        copied=dict(bad, trifecta_odds={"1-2-3":10})
        self.assertFalse(is_safe_record(copied,KEY))

    def test_network_error_rejects_without_fabricating_source_value(self):
        bad=rejected_document(key=KEY,url=URL,deadline="12:19",
            checked_at=TIME,error="ReadTimeout: official source not reachable")
        self.assertIsNone(bad["observed_numeric_count"])
        self.assertIsNone(bad["fetched_at"])
        self.assertTrue(is_safe_record(bad,KEY))

    def test_newer_failure_overrides_previous_healthy_odds(self):
        good=valid_document("2026-10-12T11:40:00+09:00")
        bad=rejected_document(key=KEY,url=URL,deadline="12:19",
            checked_at="2026-10-12T11:46:00+09:00",error="valid_odds_too_few=60")
        self.assertTrue(should_replace(good,bad,KEY))
        self.assertFalse(should_replace(bad,good,KEY))
        later=valid_document("2026-10-12T11:48:00+09:00")
        self.assertTrue(should_replace(bad,later,KEY))
        self.assertFalse(should_replace(later,bad,KEY))
        self.assertFalse(should_replace(later,later,KEY))

    def test_wrong_race_and_untrusted_timestamps_fail_closed(self):
        good=valid_document()
        good["race_key"]="20261012-14-08"
        self.assertFalse(is_safe_record(good,KEY))
        good=valid_document(time="2026-10-12T11:40:00")
        self.assertFalse(is_safe_record(good,KEY))
        with self.assertRaises(ValueError):
            rejected_document(key=KEY,url="https://evil.test",deadline="12:19",
                checked_at=TIME,error="fail")


if __name__=="__main__":
    unittest.main()
