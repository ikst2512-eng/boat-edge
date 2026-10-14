"""V340 offline artifact byte chain: synthetic capture-only, no real results."""
from datetime import datetime, timezone, timedelta
import json
from pathlib import Path
import sys
import tempfile
import unittest

TESTS = Path(__file__).resolve().parent
sys.path.insert(0, str(TESTS))
sys.path.insert(0, str(TESTS.parent / "scripts"))
from test_boat_edge_v236_v334_live_batch import prepare, fake_fetch, NOW
from boat_edge_v334_live_batch_runner import run
from boat_edge_v340_artifact_integrity import audit

KEY = "20261015-22-12"


def make(root):
    prepare(root)
    result = run(root, capture=True, clock=lambda: NOW, fetcher=fake_fetch)
    if result["completed_count"] != 1:
        raise AssertionError(result)
    return result


class V340ArtifactIntegrity(unittest.TestCase):
    def test_complete_mocked_three_source_chain(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "data/formal_status.json").parent.mkdir(parents=True)
            (root / "data/formal_status.json").write_text("DO_NOT_READ")
            report = make(root)
            result = audit(root, report)
            self.assertEqual(result["local_artifacts_verified"], 1)
            self.assertEqual(result["local_artifacts_rejected"], 0)
            self.assertTrue(result["all_reported_artifacts_locally_consistent"])
            self.assertTrue(result["verified"][0]["three_local_raw_html_sha_matches"])
            self.assertFalse(result["source_capture_time_independently_attested"])
            self.assertFalse(result["raw_source_identity_independently_verified"])
            self.assertFalse(result["original_exhibition_verified"])
            self.assertFalse(result["complete_actions_history_or_global_uniqueness_attested"])
            self.assertFalse(result["results_read"])
            self.assertFalse(result["formal_fresh_read"])

    def test_changed_frozen_json_cannot_pass_report_sha(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            report = make(root)
            path = root / report["completed"][0]["path"]
            path.write_bytes(path.read_bytes() + b" ")
            result = audit(root, report)
            self.assertEqual(result["local_artifacts_verified"], 0)
            self.assertIn("FROZEN_JSON_BYTES_SHA_MISMATCH", result["rejected"][0]["reason"])

    def test_changed_raw_html_cannot_pass_receipt_digest(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            report = make(root)
            raw = root / f"data/source_captures/20261015/{KEY}/boaters.html"
            raw.write_bytes(raw.read_bytes() + b"tamper")
            result = audit(root, report)
            self.assertEqual(result["local_artifacts_verified"], 0)
            self.assertIn("SOURCE_RAW_SHA256_MISMATCH", result["rejected"][0]["reason"])

    def test_changed_receipt_cannot_pass_frozen_copy(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            report = make(root)
            path = root / f"data/source_captures/20261015/{KEY}/official.receipt.json"
            obj = json.loads(path.read_text())
            obj["captured_at_jst"] = "2026-10-15T16:25:00+09:00"
            path.write_text(json.dumps(obj))
            result = audit(root, report)
            self.assertEqual(result["local_artifacts_verified"], 0)
            self.assertIn("FROZEN_RECEIPT_VS_RAW_MISMATCH", result["rejected"][0]["reason"])

    def test_symlink_capture_and_report_path_traversal_fail_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            report = make(root)
            path = root / f"data/source_captures/20261015/{KEY}/official.html"
            original = path.read_bytes()
            path.unlink()
            outside = root / "other.html"
            outside.write_bytes(original)
            path.symlink_to(outside)
            result = audit(root, report)
            self.assertIn("ARTIFACT_SYMLINK_FORBIDDEN", result["rejected"][0]["reason"])

            report["completed"][0]["path"] = "../formal_status.json"
            with self.assertRaisesRegex(ValueError, "NONCANONICAL_COMPLETED_PATH"):
                audit(root, report)

    def test_zero_freezes_are_not_success_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            result = run(root, capture=True, clock=lambda: NOW,
                         fetcher=lambda _: self.fail("NO_NETWORK"))
            checked = audit(root, result)
            self.assertEqual(checked["reported_completed"], 0)
            self.assertFalse(checked["all_reported_artifacts_locally_consistent"])
            self.assertFalse(checked["accuracy_improvement_proven"])

    def test_formal_or_replay_or_modified_modes_rejected_before_file_access(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            report = make(root)
            cases = [
                ("FORMAL", lambda p: p["window"].update(date="20261001")),
                ("RESULT_FLAG", lambda p: p.update(results_read=True)),
                ("FAKE_SHA", lambda p: p["completed"][0].update(sha256="deadbeef")),
                ("MODEL_SUBSET", lambda p: p["completed"][0].update(modes=["national_only"])),
                ("FUTURE_RACE", lambda p: p["completed"][0].update(race_key="20261015-22-11")),
            ]
            for reason, edit in cases:
                with self.subTest(reason=reason):
                    sample = json.loads(json.dumps(report))
                    edit(sample)
                    with self.assertRaises(ValueError):
                        audit(root, sample)


if __name__ == "__main__":
    unittest.main()
