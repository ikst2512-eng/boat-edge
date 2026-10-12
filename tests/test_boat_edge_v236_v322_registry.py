"""V322 fixture-only registry: no results, stable hashes and rejected rows."""
import json
import pathlib
import sys
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "scripts"))
from boat_edge_v322_site_baseline_registry import build_registry

TICKETS = ["1-2-3", "1-2-4", "1-2-5", "1-2-6", "1-3-2",
           "1-3-4", "1-3-5", "1-3-6", "1-4-2", "1-4-3"]


def record(key):
    return {
        "race_key": key,
        "scope": "SITE_REFERENCE_UNSEEN_PRE_RESULT_ONLY_NOT_FORMAL_FRESH",
        "deadline_jst": "2026-10-13T16:40:00+09:00",
        "evidence_committed_at": "2026-10-13T07:20:00+00:00",
        "formal_results_seen": False, "formal_gate_unlocked": False,
        "production_accuracy_claim": "NOT_PROVEN",
        "real_purchases_authorized": False,
        "model_id": "SITE_REFERENCE_V122",
        "top10": TICKETS, "top3": TICKETS[:3], "top5": TICKETS[:5],
        "head_top1": "1",
    }


class V322Registry(unittest.TestCase):
    def test_deterministic_registry_and_fail_closed_bad_record(self):
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            folder = root / "data/site_autopilot/v232_cohort"
            folder.mkdir(parents=True)
            good = "20261013-22-12"
            (folder / (good + ".json")).write_text(json.dumps(record(good)))
            bad = record("20261013-22-11")
            bad["evidence_committed_at"] = "2026-10-13T08:00:00+00:00"
            (folder / "20261013-22-11.json").write_text(json.dumps(bad))
            (root / "data/formal_status.json").write_text("DO_NOT_READ")
            first = build_registry(root, "20261013")
            second = build_registry(root, "20261013")
            self.assertEqual(first, second)
            self.assertEqual(first["accepted_count"], 1)
            self.assertEqual(first["rejected_count"], 1)
            self.assertEqual(first["entries"][0]["race_key"], good)
            self.assertEqual(len(first["entries"][0]["source_file_sha256"]), 64)
            self.assertEqual(len(first["entries"][0]["normalized_baseline_sha256"]), 64)
            self.assertFalse(first["results_read"])
            self.assertFalse(first["formal_fresh_read"])
            self.assertFalse(first["model_improvement_proven"])
            self.assertFalse(first["scoring_authorized"])


if __name__ == "__main__":
    unittest.main()
