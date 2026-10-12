"""V316 end-to-end mocked V315 receipts to V314 Git audit."""
from datetime import datetime, timedelta, timezone
import os
import pathlib
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "scripts"))
from boat_edge_v315_source_capture import capture_one
from boat_edge_v316_receipt_assemble import assemble

KEY = "20261013-22-12"
DEADLINE = "2026-10-13T16:40:00+09:00"
JST = timezone(timedelta(hours=9))
URLS = {
    "official": "https://www.boatrace.jp/owpc/pc/race/beforeinfo?hd=20261013&jcd=22&rno=12",
    "boaters": "https://boaters-boatrace.com/race/example",
    "kyoteibiyori": "https://kyoteibiyori.com/race/example",
}


def no_network(url):
    return ("<html>synthetic page: " + url + "</html>").encode(), "text/html", url


def populate(root, skip=()):
    for provider, url in URLS.items():
        if provider not in skip:
            capture_one(
                root, KEY, DEADLINE, provider, url,
                fetcher=no_network,
                clock=lambda: datetime(2026, 10, 13, 16, 20, tzinfo=JST),
            )


def initial_commit(root):
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    subprocess.run(["git", "add", "data/source_captures"], cwd=root, check=True)
    env = dict(os.environ,
               GIT_AUTHOR_DATE="2026-10-13T16:25:00+09:00",
               GIT_COMMITTER_DATE="2026-10-13T16:25:00+09:00")
    subprocess.run(["git", "-c", "user.name=test", "-c", "user.email=test@example.invalid",
                    "commit", "-q", "-m", "fixture"], cwd=root, env=env, check=True)


class V316Receipts(unittest.TestCase):
    def test_all_three_source_bytes_verified_not_model_promoted(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            populate(root)
            initial_commit(root)
            report = assemble(root, KEY, DEADLINE)
            self.assertTrue(report["ready_for_research_review"])
            self.assertEqual(report["evidence_audit"]["present_consistent_captures"], 3)
            self.assertEqual(report["missing_or_invalid_receipts"], {})
            self.assertEqual(report["bundle"]["captures"]["boaters"]["fields"], [])
            self.assertFalse(report["verified_race_identity_from_page"])
            self.assertFalse(report["original_exhibition_values_parsed"])
            self.assertFalse(report["actual_entry_verified"])
            self.assertFalse(report["candidate_scoring_authorized"])
            self.assertFalse(report["model_promotion_authorized"])
            self.assertFalse(report["formal_or_result_access"])

    def test_missing_and_corrupted_receipts_fail_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            populate(root, skip={"kyoteibiyori"})
            initial_commit(root)
            report = assemble(root, KEY, DEADLINE)
            self.assertFalse(report["ready_for_research_review"])
            self.assertEqual(report["missing_or_invalid_receipts"]["kyoteibiyori"], "RECEIPT_MISSING")
            self.assertIn("CAPTURE_NOT_SUPPLIED", report["evidence_audit"]["providers"]["kyoteibiyori"]["reasons"])
            receipt = root / "data/source_captures/20261013" / KEY / "boaters.receipt.json"
            receipt.write_text("{broken json", encoding="utf-8")
            report = assemble(root, KEY, DEADLINE)
            self.assertEqual(report["missing_or_invalid_receipts"]["boaters"], "INVALID_RECEIPT_JSON")
            self.assertEqual(report["evidence_audit"]["present_consistent_captures"], 1)

    def test_raw_tamper_after_git_first_commit_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            populate(root)
            initial_commit(root)
            raw = root / "data/source_captures/20261013" / KEY / "official.html"
            raw.write_bytes(b"tampered after capture")
            report = assemble(root, KEY, DEADLINE)
            self.assertFalse(report["ready_for_research_review"])
            self.assertIn("RAW_SHA256_MISMATCH",
                          report["evidence_audit"]["providers"]["official"]["reasons"])


if __name__ == "__main__":
    unittest.main()
