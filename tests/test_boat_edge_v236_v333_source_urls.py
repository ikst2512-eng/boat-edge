"""V333 source URL constructors: identity and date safety, no network."""
import pathlib
import sys
import unittest
from urllib.parse import parse_qs, urlsplit

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "scripts"))
from boat_edge_v333_source_urls import VENUES, suggested_source_urls


class V333UrlCandidates(unittest.TestCase):
    def test_two_independently_documented_provider_patterns(self):
        urls = suggested_source_urls("20261013-22-12")
        self.assertEqual(urls["official"],
                         "https://www.boatrace.jp/owpc/pc/race/beforeinfo?hd=20261013&jcd=22&rno=12")
        self.assertEqual(urls["boaters"],
                         "https://boaters-boatrace.com/race/fukuoka/2026-10-13/12R/last-minute?last-minute-content=original-tenji")
        kyotei = urlsplit(urls["kyoteibiyori"])
        self.assertEqual(kyotei.path, "/race_shusso.php")
        self.assertEqual(parse_qs(kyotei.query), {
            "hiduke": ["20261013"], "place_no": ["22"], "race_no": ["12"],
        })
        self.assertEqual(suggested_source_urls("20261012-02-09")["boaters"],
                         "https://boaters-boatrace.com/race/toda/2026-10-12/9R/last-minute?last-minute-content=original-tenji")

    def test_all_24_venues_construct_allowed_https_urls(self):
        self.assertEqual(len(VENUES), 24)
        self.assertEqual(set(VENUES), {f"{n:02d}" for n in range(1, 25)})
        for code in VENUES:
            with self.subTest(code=code):
                urls = suggested_source_urls(f"20261013-{code}-01")
                self.assertEqual(set(urls), {"official", "boaters", "kyoteibiyori"})
                self.assertTrue(all(url.startswith("https://") for url in urls.values()))

    def test_invalid_date_venue_or_formal_target_rejected(self):
        for key in ("20261313-22-12", "20261013-00-12", "20261013-22-13",
                    "20261001-22-12", "../20261013-22-12"):
            with self.subTest(key=key), self.assertRaises(ValueError):
                suggested_source_urls(key)


if __name__ == "__main__":
    unittest.main()
