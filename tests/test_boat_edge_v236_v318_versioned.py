"""V318 repeatable source receipts and freshest predeadline audit tests."""
from datetime import datetime, timedelta, timezone
import os
import pathlib
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "scripts"))
from boat_edge_v315_source_capture import capture_one
from boat_edge_v318_versioned_capture_audit import latest_consistent_bundle

KEY = "20261013-22-12"
DEADLINE = "2026-10-13T16:40:00+09:00"
JST = timezone(timedelta(hours=9))
URLS = {
    "official": "https://www.boatrace.jp/owpc/pc/race/beforeinfo?hd=20261013&jcd=22&rno=12",
    "boaters": "https://boaters-boatrace.com/race/regular-page",
    "kyoteibiyori": "https://kyoteibiyori.com/race_shusso.php?hiduke=20261013&place_no=22&race_no=12",
}


def capture(root, provider, minute, *, repeatable=True):
    return capture_one(
        root, KEY, DEADLINE, provider, URLS[provider],
        fetcher=lambda url: (("<html>synthetic page for " + provider + " at " +
                              str(minute) + " " + url + "</html>").encode(),
                             "text/html", url),
        clock=lambda: datetime(2026, 10, 13, 16, minute, tzinfo=JST),
        repeatable=repeatable,
    )


def commit_fixture(root, minute=30):
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    subprocess.run(["git", "add", "data/source_captures"], cwd=root, check=True)
    when = "2026-10-13T16:" + str(minute).zfill(2) + ":00+09:00"
    env = dict(os.environ, GIT_AUTHOR_DATE=when, GIT_COMMITTER_DATE=when)
    subprocess.run(["git", "-c", "user.name=test", "-c", "user.email=test@example.invalid",
                    "commit", "-q", "-m", "synthetic"], cwd=root, env=env, check=True)


class V318Versions(unittest.TestCase):
    def test_later_snapshot_selected_not_frozen_at_first_early_fetch(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            for provider in URLS:
                capture(root, provider, 10)
                capture(root, provider, 20)
            commit_fixture(root)
            report = latest_consistent_bundle(root, KEY, DEADLINE)
            self.assertTrue(report["all_three_documents_consistent"])
            self.assertEqual(report["evidence_audit"]["present_consistent_captures"], 3)
            self.assertEqual(report["selection"]["boaters"]["valid_versions"], 2)
            self.assertIn("162000", report["selection"]["boaters"]["selected"])
            self.assertEqual(report["bundle"]["captures"]["boaters"]["fields"], [])
            self.assertFalse(report["source_contents_parsed"])
            self.assertFalse(report["production_eligible"])
            self.assertFalse(report["scoring_authorized"])
            self.assertFalse(report["formal_or_result_access"])

    def test_tampered_latest_falls_back_to_untampered_earlier(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            for provider in URLS:
                capture(root, provider, 10)
                capture(root, provider, 20)
            commit_fixture(root)
            latest = root / "data/source_captures/20261013" / KEY / "versions" / "boaters-20261013T162000.html"
            latest.write_bytes(b"tamper, not attested")
            report = latest_consistent_bundle(root, KEY, DEADLINE)
            self.assertTrue(report["all_three_documents_consistent"])
            self.assertIn("161000", report["selection"]["boaters"]["selected"])
            self.assertEqual(report["selection"]["boaters"]["valid_versions"], 1)
            self.assertGreater(len(report["selection"]["boaters"]["rejected"]), 0)
            self.assertEqual(latest.read_bytes(), b"tamper, not attested")

    def test_missing_or_not_committed_never_counts_as_source(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            capture(root, "official", 10)
            capture(root, "boaters", 10)
            # No Git history: no source qualifies, irrespective of local receipt metadata.
            report = latest_consistent_bundle(root, KEY, DEADLINE)
            self.assertEqual(report["evidence_audit"]["present_consistent_captures"], 0)
            self.assertFalse(report["all_three_documents_consistent"])
            self.assertIsNone(report["selection"]["kyoteibiyori"]["selected"])

    def test_timestamped_names_are_immutable_and_old_legacy_still_supported(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            legacy = capture(root, "official", 10, repeatable=False)
            newer = capture(root, "official", 20, repeatable=True)
            self.assertNotEqual(legacy["relative_path"], newer["relative_path"])
            self.assertTrue((root / legacy["relative_path"]).exists())
            self.assertTrue((root / newer["relative_path"]).exists())
            with self.assertRaises(FileExistsError):
                capture(root, "official", 20, repeatable=True)
            for provider in ("boaters", "kyoteibiyori"):
                capture(root, provider, 20)
            commit_fixture(root)
            report = latest_consistent_bundle(root, KEY, DEADLINE)
            self.assertTrue(report["all_three_documents_consistent"])
            self.assertIn("162000", report["selection"]["official"]["selected"])


if __name__ == "__main__":
    unittest.main()
