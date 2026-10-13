"""V315 offline source-capture tests: mocked HTTP, no real network."""
from datetime import datetime, timedelta, timezone
import hashlib
import os
import pathlib
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "scripts"))
from boat_edge_v315_source_capture import capture_one, check_target, real_fetch, assert_source_network_allowed
from boat_edge_v314_three_source_evidence import SCHEMA, audit_bundle

KEY = "20261013-22-12"
DEADLINE = "2026-10-13T16:40:00+09:00"
JST = timezone(timedelta(hours=9))
URLS = {
    "official": "https://www.boatrace.jp/owpc/pc/race/beforeinfo?hd=20261013&jcd=22&rno=12",
    "boaters": "https://boaters-boatrace.com/race/example",
    "kyoteibiyori": "https://www.kyoteibiyori.com/race/example",
}


def clock(minute=20):
    return lambda: datetime(2026, 10, 13, 16, minute, 0, tzinfo=JST)


def fake_fetch(url):
    return ("<html>synthetic research fixture for " + url + "</html>").encode(), "text/html", url


class V315SourceCapture(unittest.TestCase):
    def test_issue_204_real_http_denies_third_party_before_any_opener(self):
        for provider in ("boaters","kyoteibiyori"):
            url=URLS[provider]
            with self.subTest(provider=provider):
                with patch("boat_edge_v315_source_capture.build_opener",
                           side_effect=AssertionError("NETWORK_MUST_NOT_START")) as opener:
                    with self.assertRaisesRegex(ValueError,"THIRD_PARTY_NETWORK_CAPTURE_PAUSED_NO_VERIFIED_GRANT"):
                        real_fetch(url)
                    opener.assert_not_called()
                    with tempfile.TemporaryDirectory() as directory:
                        with self.assertRaisesRegex(ValueError,"THIRD_PARTY_NETWORK_CAPTURE_PAUSED_NO_VERIFIED_GRANT"):
                            capture_one(pathlib.Path(directory), KEY, DEADLINE, provider,
                                        url, clock=clock())
                        self.assertFalse((pathlib.Path(directory)/"data/source_captures").exists())
                    opener.assert_not_called()
        self.assertEqual(assert_source_network_allowed(URLS["official"]),URLS["official"])

    def test_one_page_is_immutable_and_fields_not_inferred(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            capture = capture_one(root, KEY, DEADLINE, "boaters", URLS["boaters"],
                                  fetcher=fake_fetch, clock=clock())
            path = root / capture["relative_path"]
            self.assertTrue(path.is_file())
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), capture["sha256"])
            self.assertEqual(capture["fields"], [])
            with self.assertRaises(ValueError):
                capture_one(root, KEY, DEADLINE, "boaters", URLS["boaters"],
                            fetcher=fake_fetch, clock=clock())
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), capture["sha256"])

    def test_three_mocked_pages_fit_v314_document_bundle_after_git_commit(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            captures = {
                provider: capture_one(root, KEY, DEADLINE, provider, url,
                                      fetcher=fake_fetch, clock=clock())
                for provider, url in URLS.items()
            }
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            subprocess.run(["git", "add", "data/source_captures"], cwd=root, check=True)
            env = dict(os.environ, GIT_AUTHOR_DATE="2026-10-13T16:23:00+09:00",
                       GIT_COMMITTER_DATE="2026-10-13T16:23:00+09:00")
            subprocess.run(["git", "-c", "user.name=test", "-c", "user.email=test@example.invalid",
                            "commit", "-q", "-m", "synthetic"], cwd=root, env=env, check=True)
            report = audit_bundle(root, {
                "schema": SCHEMA, "race_key": KEY, "deadline_jst": DEADLINE, "captures": captures,
            })
            self.assertEqual(report["present_consistent_captures"], 3)
            self.assertTrue(report["all_three_document_bundles_consistent"])
            self.assertFalse(report["original_exhibition_parsed_and_verified"])
            self.assertFalse(report["independently_verified_actual_entry"])
            self.assertFalse(report["candidate_model_promotion_authorized"])

    def test_prohibited_hosts_results_and_official_wrong_race(self):
        with self.assertRaises(ValueError):
            check_target("boaters", "https://boaters-boatrace.com.attacker.invalid/race", KEY)
        with self.assertRaises(ValueError):
            check_target("boaters", "https://boaters-boatrace.com/race/result", KEY)
        with self.assertRaises(ValueError):
            check_target("kyoteibiyori", "https://kyoteibiyori.com/race?view=%E6%89%95%E6%88%BB", KEY)
        with self.assertRaises(ValueError):
            check_target("official", URLS["official"].replace("jcd=22", "jcd=23"), KEY)
        with self.assertRaises(ValueError):
            check_target("official", "https://www.boatrace.jp/owpc/pc/race/raceresult?hd=20261013&jcd=22&rno=12", KEY)
        with self.assertRaises(ValueError):
            check_target("boaters", "https://boaters-boatrace.com/", KEY)

    def test_late_bad_http_redirect_and_short_content_not_saved(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            cases = [
                (clock(41), fake_fetch),
                (clock(20), lambda url: (b"<html>short</html>", "text/html", url)),
                (clock(20), lambda url: (b"x" * 100, "application/json", url)),
                (clock(20), lambda url: (b"x" * 100, "text/html", url + "/redirect")),
            ]
            for ck, fetcher in cases:
                with self.subTest(ck=ck, fetcher=fetcher):
                    with self.assertRaises(ValueError):
                        capture_one(root, KEY, DEADLINE, "boaters", URLS["boaters"],
                                    fetcher=fetcher, clock=ck)
                    self.assertFalse((root / "data/source_captures/20261013" / KEY / "boaters.html").is_file())

    def test_crossing_deadline_mid_fetch_does_not_write(self):
        times = iter([clock(20)(), clock(41)()])
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(ValueError):
                capture_one(pathlib.Path(directory), KEY, DEADLINE, "official", URLS["official"],
                            fetcher=fake_fetch, clock=lambda: next(times))


if __name__ == "__main__":
    unittest.main()
