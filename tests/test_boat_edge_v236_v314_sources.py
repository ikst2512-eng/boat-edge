"""V314 synthetic-only, fixture Git provenance and source security gates."""
import hashlib
import os
import pathlib
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "scripts"))
from boat_edge_v314_three_source_evidence import (
    SCHEMA, audit_bundle, domain_matches,
)

KEY = "20261013-22-12"
DOMAINS = {
    "official": "www.boatrace.jp",
    "boaters": "boaters-boatrace.com",
    "kyoteibiyori": "kyoteibiyori.com",
}


def fixture(root):
    captures = {}
    for provider, domain in DOMAINS.items():
        path = pathlib.Path("data/source_captures/20261013") / KEY / (provider + ".html")
        raw = ("<html>synthetic test: " + provider + "</html>").encode("utf-8")
        target = root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)
        captures[provider] = {
            "source_url": "https://" + domain + "/some/race/path",
            "race_key": KEY,
            "captured_at_jst": "2026-10-13T16:20:00+09:00",
            "sha256": hashlib.sha256(raw).hexdigest(),
            "relative_path": path.as_posix(),
            "fields": ["lap_time", "turn_time", "straight_time"],
        }
    return {
        "schema": SCHEMA,
        "race_key": KEY,
        "deadline_jst": "2026-10-13T16:40:00+09:00",
        "captures": captures,
    }


def commit_repo(root, when="2026-10-13T16:25:00+09:00"):
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    subprocess.run(["git", "add", "data/source_captures"], cwd=root, check=True)
    env = dict(os.environ, GIT_AUTHOR_DATE=when, GIT_COMMITTER_DATE=when)
    subprocess.run(["git", "-c", "user.name=test", "-c", "user.email=test@example.invalid",
                    "commit", "-q", "-m", "synthetic sources"], cwd=root, env=env, check=True)


class V314CaptureEvidence(unittest.TestCase):
    def test_complete_three_provider_bundle_is_only_document_consistent(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            bundle = fixture(root)
            commit_repo(root)
            result = audit_bundle(root, bundle)
            self.assertEqual(result["present_consistent_captures"], 3)
            self.assertTrue(result["all_three_document_bundles_consistent"])
            self.assertFalse(result["independent_capture_time_authenticated"])
            self.assertFalse(result["original_exhibition_parsed_and_verified"])
            self.assertFalse(result["independently_verified_actual_entry"])
            self.assertFalse(result["candidate_model_promotion_authorized"])
            self.assertFalse(result["result_or_formal_access"])

    def test_missing_late_modified_and_wrong_identity_fail_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            bundle = fixture(root)
            commit_repo(root)
            bundle["captures"]["kyoteibiyori"]["captured_at_jst"] = "2026-10-13T16:41:00+09:00"
            report = audit_bundle(root, bundle)
            self.assertIn("CAPTURE_NOT_PREDEADLINE", report["providers"]["kyoteibiyori"]["reasons"])
            bundle["captures"]["kyoteibiyori"]["captured_at_jst"] = "2026-10-13T16:20:00+09:00"
            bundle["captures"]["boaters"]["race_key"] = "20261013-22-11"
            report = audit_bundle(root, bundle)
            self.assertIn("RACE_IDENTITY_DECLARATION_MISMATCH", report["providers"]["boaters"]["reasons"])
            bundle["captures"]["boaters"]["race_key"] = KEY
            (root / bundle["captures"]["official"]["relative_path"]).write_bytes(b"tamper")
            report = audit_bundle(root, bundle)
            self.assertIn("RAW_SHA256_MISMATCH", report["providers"]["official"]["reasons"])
            bundle["captures"].pop("official")
            report = audit_bundle(root, bundle)
            self.assertIn("CAPTURE_NOT_SUPPLIED", report["providers"]["official"]["reasons"])
            self.assertFalse(report["all_three_document_bundles_consistent"])

    def test_block_fake_host_path_injection_and_result_field(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            bundle = fixture(root)
            commit_repo(root)
            self.assertFalse(domain_matches("boaters", "https://boaters-boatrace.com.evil.test/race"))
            bundle["captures"]["boaters"]["source_url"] = "https://boaters-boatrace.com.evil.test/race"
            bundle["captures"]["official"]["relative_path"] = "../../secret"
            bundle["captures"]["kyoteibiyori"]["fields"] = ["result"]
            report = audit_bundle(root, bundle)
            self.assertIn("WRONG_PROVIDER_DOMAIN", report["providers"]["boaters"]["reasons"])
            self.assertIn("CAPTURE_PATH_NOT_CANONICAL", report["providers"]["official"]["reasons"])
            self.assertIn("UNVERIFIED_FIELD_DECLARATION", report["providers"]["kyoteibiyori"]["reasons"])

    def test_git_first_committed_after_deadline_not_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            bundle = fixture(root)
            commit_repo(root, when="2026-10-13T16:45:00+09:00")
            report = audit_bundle(root, bundle)
            self.assertEqual(report["present_consistent_captures"], 0)
            self.assertTrue(all(
                "FIRST_GIT_BYTES_OR_TIMESTAMP_NOT_ATTESTED" in row["reasons"]
                for row in report["providers"].values()
            ))

    def test_bad_bundle_schema_and_unknown_source(self):
        with tempfile.TemporaryDirectory() as directory:
            bundle = fixture(pathlib.Path(directory))
            bundle["captures"]["untrusted"] = {}
            with self.assertRaises(ValueError):
                audit_bundle(pathlib.Path(directory), bundle)
            bundle["captures"].pop("untrusted")
            bundle["result"] = "1-2-3"
            with self.assertRaises(ValueError):
                audit_bundle(pathlib.Path(directory), bundle)


if __name__ == "__main__":
    unittest.main()
