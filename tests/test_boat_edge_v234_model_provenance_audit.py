import json
import tempfile
import unittest
from pathlib import Path
from scripts.boat_edge_v234_model_provenance_audit import audit


class ModelProvenanceTests(unittest.TestCase):
    def test_missing_sha_not_promoted(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            d = root / "data/site_autopilot/v232_cohort"
            d.mkdir(parents=True)
            key = "20261025-21-01"
            p = d / (key + ".json")
            p.write_text(json.dumps({"race_key": key, "model_id": "SITE_REFERENCE_V122"}))
            result = audit(root)
            self.assertEqual(result["coverage_counts"]["model_git_sha_missing_or_invalid"], 1)
            self.assertFalse(result["accuracy_improvement_proven"])
            self.assertFalse(result["model_source_independently_verified"])
            record = {"race_key": key, "model_id": "SITE_REFERENCE_V122",
                      "model_git_sha": "a" * 40, "model_source_sha256": "b" * 64}
            p.write_text(json.dumps(record))
            new = audit(root)
            self.assertEqual(new["coverage_counts"]["declared_hashes_present_not_independently_verified"], 1)


if __name__ == "__main__":
    unittest.main()
