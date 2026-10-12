"""V323 race source SHA evidence checks without results access."""
import hashlib
import json
import pathlib
import sys
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "scripts"))
from boat_edge_v323_site_source_sha import inspect_source

KEY = "20261013-22-12"
TICKETS = ["1-2-3", "1-2-4", "1-2-5", "1-2-6", "1-3-2",
           "1-3-4", "1-3-5", "1-3-6", "1-4-2", "1-4-3"]


def create_fixture(root):
    race = {
        "race_key": KEY,
        "source_audit": {
            "race_card": {"status": "ok"},
            "beforeinfo": {"status": "not_in_window"},
        },
        "beforeinfo": {},
    }
    raw = json.dumps(race).encode()
    race_file = root / "data/races" / (KEY + ".json")
    race_file.parent.mkdir(parents=True)
    race_file.write_bytes(raw)
    baseline = {
        "race_key": KEY,
        "scope": "SITE_REFERENCE_UNSEEN_PRE_RESULT_ONLY_NOT_FORMAL_FRESH",
        "deadline_jst": "2026-10-13T16:40:00+09:00",
        "evidence_committed_at": "2026-10-13T07:20:00+00:00",
        "formal_results_seen": False, "formal_gate_unlocked": False,
        "production_accuracy_claim": "NOT_PROVEN",
        "real_purchases_authorized": False,
        "model_id": "SITE_REFERENCE_V122",
        "top10": TICKETS, "top3": TICKETS[:3], "top5": TICKETS[:5],
        "head_top1": "1",
        "source_race_sha256": hashlib.sha256(raw).hexdigest(),
    }
    folder = root / "data/site_autopilot/v232_cohort"
    folder.mkdir(parents=True)
    (folder / (KEY + ".json")).write_text(json.dumps(baseline))
    return race_file


class V323SourceSha(unittest.TestCase):
    def test_match_and_no_authenticity_claim(self):
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            create_fixture(root)
            (root / "data/formal_status.json").write_text("NOT_JSON_DO_NOT_READ")
            report = inspect_source(root, KEY)
            self.assertTrue(report["source_race_file_byte_match"])
            self.assertEqual(report["beforeinfo_status"], "not_in_window")
            self.assertFalse(report["original_exhibition_three_sources_verified"])
            self.assertFalse(report["race_actual_entry_independently_verified"])
            self.assertFalse(report["results_read"])
            self.assertFalse(report["formal_fresh_read"])

    def test_tamper_detected(self):
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            path = create_fixture(root)
            data = json.loads(path.read_text())
            data["source_audit"]["beforeinfo"]["status"] = "ok"
            path.write_text(json.dumps(data))
            report = inspect_source(root, KEY)
            self.assertFalse(report["source_race_file_byte_match"])

    def test_invalid_race_key(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError):
                inspect_source(pathlib.Path(d), "../../formal_status")


if __name__ == "__main__":
    unittest.main()
