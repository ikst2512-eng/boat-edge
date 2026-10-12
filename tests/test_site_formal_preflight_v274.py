import itertools
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from site_formal_preflight_v274 import check, _sha
from site_v179_patch import audit

SHA = "a" * 64
PARENT = "b" * 64
G = {"results_seen": False, "unlock": False, "scoring": False, "RESULT_UNLOCK_TOKEN": None}


class FormalPreflightV274(unittest.TestCase):
    def create(self, root):
        base = root / "data" / "formal_predictions"
        base.mkdir(parents=True)
        rank = [{"combo": "-".join(c), "probability": 1 / 120} for c in itertools.permutations("123456", 3)]
        derived = {"ranked_120": rank,
                   "world_a": {"probability": 0.5, "tickets": [{"combo": "1-2-3", "amount": 5000}]},
                   "world_b": {"probability": 0.5, "tickets": [{"combo": "2-1-3", "amount": 5000}]}}
        digest = _sha(derived)
        mapping = {}
        for i in range(100):
            key = f"20261013-{i // 12 + 1:02}-{i % 12 + 1:02}"
            mapping[key] = digest
            obj = {"formal_meta": {"schema_version": "boat-edge-formal-approved-overlay-v1",
                   "race_key": key, "model_id": "MODEL-APPROVED",
                   "scope": "FORMAL_FRESH_APPROVED_PRE_RESULT", "model_approved": True,
                   "formal_gate_pass": True, "freeze_sha256": SHA, "prediction_sha256": digest,
                   "parent_sha256": PARENT, "guards": dict(G)}, "derived": derived}
            (base / (key + ".json")).write_text(json.dumps(obj))
        status = {"target_date": "2026-10-13", "formalParentSha": PARENT,
                  "active_model_id": "MODEL-APPROVED", "guards": dict(G),
                  "formalFirst100": {"races": 100, "freezeManifestSha": SHA, "coreSha": SHA},
                  "connected": True, "predictions_ready": True,
                  "approved_prediction_sha256_by_race": mapping}
        (root / "data" / "formal_status.json").write_text(json.dumps(status))
        (root / "data" / "model_status.json").write_text(json.dumps({
            "target_date": "2026-10-13", "formal_parent_sha256": PARENT,
            "core7": {"eligible_count": 144, "core7_100_ready": True}}))
        (root / "data" / "site_latest_bridge_contract.json").write_text('{"version":"V177"}')
        return status, base

    def test_valid_synthetic_100_is_only_site_preflight(self):
        with tempfile.TemporaryDirectory() as d:
            status, _ = self.create(Path(d))
            self.assertEqual(check(d, status), (True, 100, "VERIFIED_100_SITE_PREFLIGHT_ONLY"))
            report = audit(Path(d))
            self.assertTrue(report["formal_prediction_content_preflight_passed"])
            self.assertEqual(report["formal_prediction_content_verified_files"], 100)

    def test_wrong_freeze_manifest_rejected_even_with_valid_sha_shape(self):
        with tempfile.TemporaryDirectory() as d:
            status, base = self.create(Path(d))
            path = sorted(base.glob("*.json"))[0]
            v = json.loads(path.read_text())
            v["formal_meta"]["freeze_sha256"] = "c" * 64
            path.write_text(json.dumps(v))
            self.assertEqual(check(d, status)[2], "PREDICTION_METADATA_INVALID")
            report = audit(Path(d))
            self.assertFalse(report["site_consumer_ready_to_display_actual_formal_predictions"])

    def test_unfrozen_status_rejected_even_with_100_approved_files(self):
        with tempfile.TemporaryDirectory() as d:
            status, _ = self.create(Path(d))
            status["formalFirst100"]["races"] = 0
            self.assertEqual(check(d, status)[2], "FORMAL_COHORT_NOT_FROZEN_100")

    def test_missing_core_sha_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            status, _ = self.create(Path(d))
            status["formalFirst100"]["coreSha"] = None
            self.assertEqual(check(d, status)[2], "FORMAL_COHORT_NOT_FROZEN_100")

    def test_duplicate_json_metadata_key_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            status, base = self.create(Path(d))
            path = sorted(base.glob("*.json"))[0]
            raw = path.read_text()
            self.assertIn('"formal_meta": {', raw)
            raw = raw.replace('"formal_meta": {', '"formal_meta": {"model_approved": false, ', 1)
            path.write_text(raw)
            self.assertEqual(check(d, status)[2], "PREDICTION_JSON_INVALID")
            report = audit(Path(d))
            self.assertFalse(report["site_consumer_ready_to_display_actual_formal_predictions"])

    def test_duplicate_json_derived_key_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            status, base = self.create(Path(d))
            path = sorted(base.glob("*.json"))[0]
            raw = path.read_text()
            self.assertIn('"derived": {', raw)
            raw = raw.replace('"derived": {', '"derived": {"ranked_120": [], ', 1)
            path.write_text(raw)
            self.assertEqual(check(d, status)[2], "PREDICTION_JSON_INVALID")

    def test_digest_map_missing_fails_closed(self):
        with tempfile.TemporaryDirectory() as d:
            status, _ = self.create(Path(d))
            del status["approved_prediction_sha256_by_race"]
            self.assertEqual(check(d, status)[2], "APPROVED_RACE_SHA_MAP_NOT_100")

    def test_content_tamper_fails_closed(self):
        with tempfile.TemporaryDirectory() as d:
            status, base = self.create(Path(d))
            path = sorted(base.glob("*.json"))[0]
            v = json.loads(path.read_text())
            v["derived"]["world_a"]["tickets"][0]["amount"] = 4900
            path.write_text(json.dumps(v))
            self.assertEqual(check(d, status)[2], "PREDICTION_CONTENT_SHA_MISMATCH")
            report = audit(Path(d))
            self.assertFalse(report["site_consumer_ready_to_display_actual_formal_predictions"])
            self.assertIn("FORMAL_PREDICTION_CONTENT_PRECHECK_FAILED", report["blockers"])

    def test_wrong_race_file_set_fails_closed(self):
        with tempfile.TemporaryDirectory() as d:
            status, base = self.create(Path(d))
            sorted(base.glob("*.json"))[0].rename(base / "20261014-01-01.json")
            self.assertEqual(check(d, status)[2], "APPROVED_RACE_FILE_SET_MISMATCH")

    def test_results_seen_guard_fails_closed(self):
        with tempfile.TemporaryDirectory() as d:
            status, _ = self.create(Path(d))
            status["guards"]["results_seen"] = True
            self.assertEqual(check(d, status)[2], "STATUS_PRE_RESULT_GUARD_INVALID")

    def test_missing_file_fails_closed(self):
        with tempfile.TemporaryDirectory() as d:
            status, base = self.create(Path(d))
            sorted(base.glob("*.json"))[0].unlink()
            self.assertEqual(check(d, status)[2], "APPROVED_RACE_FILE_SET_MISMATCH")

    def test_model_mismatch_fails_closed(self):
        with tempfile.TemporaryDirectory() as d:
            status, base = self.create(Path(d))
            path = sorted(base.glob("*.json"))[0]
            v = json.loads(path.read_text())
            v["formal_meta"]["model_id"] = "WRONG"
            path.write_text(json.dumps(v))
            self.assertEqual(check(d, status)[2], "PREDICTION_METADATA_INVALID")

    def test_invalid_rank120_fails_even_with_updated_sha(self):
        with tempfile.TemporaryDirectory() as d:
            status, base = self.create(Path(d))
            path = sorted(base.glob("*.json"))[0]
            v = json.loads(path.read_text())
            v["derived"]["ranked_120"][0]["combo"] = v["derived"]["ranked_120"][1]["combo"]
            digest = _sha(v["derived"])
            status["approved_prediction_sha256_by_race"][path.stem] = digest
            v["formal_meta"]["prediction_sha256"] = digest
            path.write_text(json.dumps(v))
            self.assertEqual(check(d, status)[2], "PREDICTION_RANK_OR_STAKE_INVALID")

    def test_nonstring_ticket_is_rejected_not_exception(self):
        with tempfile.TemporaryDirectory() as d:
            status, base = self.create(Path(d))
            path = sorted(base.glob("*.json"))[0]
            v = json.loads(path.read_text())
            v["derived"]["world_a"]["tickets"][0]["combo"] = ["1", "2", "3"]
            digest = _sha(v["derived"])
            status["approved_prediction_sha256_by_race"][path.stem] = digest
            v["formal_meta"]["prediction_sha256"] = digest
            path.write_text(json.dumps(v))
            self.assertEqual(check(d, status)[2], "PREDICTION_RANK_OR_STAKE_INVALID")


if __name__ == "__main__":
    unittest.main()
