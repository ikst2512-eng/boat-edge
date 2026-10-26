"""Synthetic-only prospective pair gate tests."""
import hashlib
import tempfile
import unittest
from pathlib import Path
from check_prospective_pair_bundle import check


class PairedBundleTests(unittest.TestCase):
    def test_missing_baseline_never_scores(self):
        with tempfile.TemporaryDirectory() as d:
            result = check(d, {"scope": "RESEARCH_PRE_RESULT_ONLY", "candidate": {}})
            self.assertFalse(result["ready_for_scoring"])
            self.assertIn("MISSING_BASELINE", result["errors"])

    def test_identical_inputs_still_require_independent_receipt(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "snapshot.bin"
            path.write_bytes(b"synthetic pre-result only")
            sha = hashlib.sha256(path.read_bytes()).hexdigest()
            refs = {name: {"path": "snapshot.bin", "sha256": sha}
                    for name in ("input", "model", "prediction")}
            manifest = {"scope": "RESEARCH_PRE_RESULT_ONLY",
                        "baseline": dict(refs), "candidate": dict(refs)}
            result = check(d, manifest)
            self.assertEqual(result["local_byte_integrity"], "PASS")
            self.assertFalse(result["ready_for_scoring"])
            self.assertIn("INDEPENDENT_PREDEADLINE_RECEIPT_MISSING", result["errors"])

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
