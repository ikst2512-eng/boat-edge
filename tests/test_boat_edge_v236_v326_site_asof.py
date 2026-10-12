"""V326 postdeadline snapshot detection, with matching bytes and no results."""
import hashlib
import json
import pathlib
import sys
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "scripts"))
from boat_edge_v326_site_asof_audit import asof_audit

KEY = "20261013-22-12"
T = ["1-2-3", "1-2-4", "1-2-5", "1-2-6", "1-3-2",
     "1-3-4", "1-3-5", "1-3-6", "1-4-2", "1-4-3"]


def prepare(root, updated, fetched):
    race = {"race_key": KEY, "meta": {
        "phase": "PRE_RESULT", "updated_at": updated,
        "results_seen": False, "unlock": False, "scoring": False},
        "source_audit": {"race_card": {"status": "ok", "fetched_at": fetched}}}
    raw = json.dumps(race).encode()
    path = root / "data/races" / (KEY + ".json")
    path.parent.mkdir(parents=True)
    path.write_bytes(raw)
    baseline = {
        "race_key": KEY,
        "scope": "SITE_REFERENCE_UNSEEN_PRE_RESULT_ONLY_NOT_FORMAL_FRESH",
        "deadline_jst": "2026-10-13T16:40:00+09:00",
        "evidence_committed_at": "2026-10-13T07:20:00+00:00",
        "formal_results_seen": False, "formal_gate_unlocked": False,
        "production_accuracy_claim": "NOT_PROVEN",
        "real_purchases_authorized": False, "model_id": "SITE_REFERENCE_V122",
        "top10": T, "top3": T[:3], "top5": T[:5], "head_top1": "1",
        "source_race_sha256": hashlib.sha256(raw).hexdigest()}
    folder = root / "data/site_autopilot/v232_cohort"
    folder.mkdir(parents=True)
    (folder / (KEY + ".json")).write_text(json.dumps(baseline))


class V326AsOf(unittest.TestCase):
    def test_late_snapshot_rejected_even_when_sha_matches(self):
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            prepare(root, "2026-10-13T23:49:00+09:00",
                    "2026-10-13T23:51:00+09:00")
            (root / "data/formal_status.json").write_text("DO_NOT_READ")
            report = asof_audit(root, KEY)
            self.assertTrue(report["source_race_file_byte_match"])
            self.assertFalse(report["asof_predeadline_usable"])
            self.assertIn("POSTDEADLINE_TIMESTAMP:meta.updated_at", report["issues"])
            self.assertIn("POSTDEADLINE_TIMESTAMP:source_audit.race_card.fetched_at", report["issues"])
            self.assertFalse(report["formal_fresh_read"])

    def test_early_metadata_can_pass_but_no_independent_auth(self):
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            prepare(root, "2026-10-13T16:31:00+09:00",
                    "2026-10-13T16:30:00+09:00")
            report = asof_audit(root, KEY)
            self.assertTrue(report["asof_predeadline_usable"])
            self.assertFalse(report["independent_source_authentication_proven"])
            self.assertFalse(report["model_accuracy_proven"])


if __name__ == "__main__":
    unittest.main()
