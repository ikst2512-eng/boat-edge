"""Synthetic strict V332 inventory regression tests only."""
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from inventory_v332_strict import inspect_strict


class StrictInventoryTests(unittest.TestCase):
    def test_missing(self):
        with tempfile.TemporaryDirectory() as folder:
            report = inspect_strict(folder, "20261026")
            self.assertEqual(report["local_digest_verified_count"], 0)
            self.assertEqual(report["comparable_for_scoring"], 0)

    def test_tampered_digest_not_counted(self):
        with tempfile.TemporaryDirectory() as folder:
            p = Path(folder) / "data/research_local_v332/20261026"
            p.mkdir(parents=True)
            key = "20261026-06-08"
            candidate = {"synthetic": "only"}
            digest = hashlib.sha256(json.dumps(candidate, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode()).hexdigest()
            obj = {"race_key": key, "model_id": "BOAT_EDGE_V332_LIVE_LOCAL_SHA_RESEARCH_ONLY",
                   "frozen_at_jst": "2026-10-26T13:59:00+09:00",
                   "deadline_jst": "2026-10-26T14:06:00+09:00",
                   "evidence_level": "LOCAL_RECEIPT_RAW_SHA_ONLY",
                   "scoring_authorized": False, "race_source_sha256": "a" * 64,
                   "candidate_sha256": digest, "candidate": candidate,
                   "results_read": False, "formal_fresh_read": False}
            output = p / (key + ".json")
            output.write_text(json.dumps(obj), encoding="utf-8")
            good = inspect_strict(folder, "20261026")
            self.assertEqual(good["local_digest_verified_count"], 1)
            self.assertEqual(good["comparable_for_scoring"], 0)
            obj["candidate"] = {"synthetic": "tampered"}
            output.write_text(json.dumps(obj), encoding="utf-8")
            bad = inspect_strict(folder, "20261026")
            self.assertEqual(bad["weak_schema_only_count"], 1)
            self.assertEqual(bad["local_digest_verified_count"], 0)
            self.assertEqual(bad["invalid"][0]["reason"], "V332_CANDIDATE_SHA_MISMATCH")


if __name__ == "__main__":
    unittest.main()
