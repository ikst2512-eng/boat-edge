"""Synthetic-only prospective pair gate tests."""
import hashlib
import tempfile
import unittest
from pathlib import Path
from check_prospective_pair_bundle import check


class PairedBundleTests(unittest.TestCase):
    def test_missing_race_identity_blocks_integrity_pass(self):
        with tempfile.TemporaryDirectory() as d:
            report = check(d, {"scope": "RESEARCH_PRE_RESULT_ONLY"})
            self.assertIn("RACE_KEY_REQUIRED", report["errors"])
            self.assertIn("VALID_RACE_DEADLINE_REQUIRED", report["errors"])
            self.assertNotIn("local_byte_integrity", report)

    def test_malformed_race_id_fails_closed(self):
        with tempfile.TemporaryDirectory() as d:
            for bad in (None, 123, "", "20261027-99-99"):
                report = check(d, {"scope": "RESEARCH_PRE_RESULT_ONLY",
                                   "race_key": bad, "deadline_jst": "2026-10-27T14:06:00+09:00"})
                self.assertIn("RACE_KEY_REQUIRED", report["errors"])
                self.assertFalse(report["ready_for_scoring"])

    def test_deadline_wrong_timezone_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            report = check(d, {"scope": "RESEARCH_PRE_RESULT_ONLY",
                               "race_key": "20261027-06-08",
                               "deadline_jst": "2026-10-27T05:06:00+00:00"})
            self.assertIn("VALID_RACE_DEADLINE_REQUIRED", report["errors"])
            self.assertFalse(report["ready_for_scoring"])

    def test_missing_baseline_never_scores(self):
        with tempfile.TemporaryDirectory() as d:
            result = check(d, {"race_key": "20261027-06-08", "deadline_jst": "2026-10-27T14:06:00+09:00", "scope": "RESEARCH_PRE_RESULT_ONLY", "candidate": {}})
            self.assertFalse(result["ready_for_scoring"])
            self.assertIn("MISSING_BASELINE", result["errors"])

    def test_identical_inputs_still_require_independent_receipt(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "snapshot.bin"
            path.write_bytes(b"synthetic pre-result only")
            sha = hashlib.sha256(path.read_bytes()).hexdigest()
            refs = {}
            for name in ("input", "model", "prediction"):
                filename = name + ".bin"
                (Path(d) / filename).write_bytes(b"synthetic pre-result only")
                refs[name] = {"path": filename, "sha256": sha}
            manifest = {"scope": "RESEARCH_PRE_RESULT_ONLY",
                        "race_key": "20261027-06-08",
                        "deadline_jst": "2026-10-27T14:06:00+09:00",
                        "baseline": dict(refs), "candidate": dict(refs)}
            result = check(d, manifest)
            self.assertEqual(result["local_byte_integrity"], "PASS")
            self.assertFalse(result["ready_for_scoring"])
            self.assertIn("INDEPENDENT_PREDEADLINE_RECEIPT_MISSING", result["errors"])

    def test_aliased_roles_are_not_proof(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "only.bin"
            p.write_bytes(b"fake combined evidence")
            ref = {"path": "only.bin", "sha256": hashlib.sha256(p.read_bytes()).hexdigest()}
            manifest = {"scope": "RESEARCH_PRE_RESULT_ONLY",
                        "baseline": {"input": ref, "model": ref, "prediction": ref},
                        "candidate": {"input": ref, "model": ref, "prediction": ref}}
            result = check(d, manifest)
            self.assertIn("ALIASED_INPUT_MODEL_PREDICTION", result["errors"])
            self.assertFalse(result["ready_for_scoring"])

    def test_input_digest_mismatch_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            refs = {}
            for name, content in (("left", b"race input one"), ("right", b"race input two")):
                p = Path(d) / (name + ".bin")
                p.write_bytes(content)
                refs[name] = {"path": p.name, "sha256": hashlib.sha256(content).hexdigest()}
            for name in ("model.bin", "prediction.bin"):
                p = Path(d) / name
                p.write_bytes(name.encode())
                refs[name] = {"path": name, "sha256": hashlib.sha256(name.encode()).hexdigest()}
            def side(input_name):
                return {"input": refs[input_name], "model": refs["model.bin"],
                        "prediction": refs["prediction.bin"]}
            report = check(d, {"race_key": "20261027-06-08", "deadline_jst": "2026-10-27T14:06:00+09:00", "scope": "RESEARCH_PRE_RESULT_ONLY",
                               "baseline": side("left"), "candidate": side("right")})
            self.assertIn("INPUT_NOT_IDENTICAL", report["errors"])
            self.assertFalse(report["ready_for_scoring"])

    def test_traversal_rejected_without_reading(self):
        with tempfile.TemporaryDirectory() as d:
            src = {"path": "../outside.bin", "sha256": "0" * 64}
            side = {"input": src, "model": src, "prediction": src}
            report = check(d, {"race_key": "20261027-06-08", "deadline_jst": "2026-10-27T14:06:00+09:00", "scope": "RESEARCH_PRE_RESULT_ONLY",
                               "baseline": side, "candidate": side})
            self.assertIn("UNSAFE_REFERENCE", report["errors"])
            self.assertFalse(report["ready_for_scoring"])

    def test_modified_bytes_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "snapshot.bin"
            p.write_bytes(b"different")
            src = {"path": "snapshot.bin", "sha256": "0" * 64}
            manifest = {"scope": "RESEARCH_PRE_RESULT_ONLY",
                        "baseline": {"input": src, "model": src, "prediction": src},
                        "candidate": {"input": src, "model": src, "prediction": src}}
            result = check(d, manifest)
            self.assertIn("SHA_MISMATCH", result["errors"])
            self.assertFalse(result["ready_for_scoring"])

if __name__ == "__main__":
    unittest.main()
