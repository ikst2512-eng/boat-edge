"""Digest integrity checks are not race eligibility or public-time evidence."""
import hashlib
import json
import unittest
from verify_v332_candidate_digest import verify_candidate_digest


def digest(obj):
    raw = json.dumps(obj, sort_keys=True, ensure_ascii=False,
                     separators=(",", ":"), allow_nan=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


class CandidateDigestTests(unittest.TestCase):
    def test_valid_canonical_digest(self):
        c = {"race_key": "synthetic", "predictions": [1, 2, 3]}
        self.assertTrue(verify_candidate_digest({"candidate": c, "candidate_sha256": digest(c)}))

    def test_key_order_is_irrelevant(self):
        a = {"x": 1, "y": 2}
        b = {"y": 2, "x": 1}
        self.assertEqual(digest(a), digest(b))

    def test_tampering_rejected(self):
        c = {"predictions": [1, 2]}
        with self.assertRaisesRegex(ValueError, "V332_CANDIDATE_SHA_MISMATCH"):
            verify_candidate_digest({"candidate": {"predictions": [2, 1]}, "candidate_sha256": digest(c)})

    def test_nonfinite_rejected(self):
        with self.assertRaisesRegex(ValueError, "V332_CANDIDATE_NOT_CANONICAL"):
            verify_candidate_digest({"candidate": {"prob": float("nan")}, "candidate_sha256": "0" * 64})

    def test_missing_rejected(self):
        with self.assertRaisesRegex(ValueError, "V332_CANDIDATE_DIGEST_MISSING"):
            verify_candidate_digest({"candidate": {}})


if __name__ == "__main__":
    unittest.main()
