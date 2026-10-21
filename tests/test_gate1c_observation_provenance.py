"""Synthetic-only Gate 1C observation provenance regression. No real races/results."""
import hashlib
import importlib.util
import json
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("v220_provenance", ROOT / "scripts/boat_edge_v220_site_ops.py")
MOD = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MOD)


class ObservationProvenanceTest(unittest.TestCase):
    def test_history_digest_tracks_exact_source_and_fail_closes_missing(self):
        with TemporaryDirectory() as folder:
            root = Path(folder)
            day = "20261021"
            now = datetime(2026, 10, 21, 10, 0, tzinfo=timezone.utc)
            path = root / "data/site_paper_sim/readiness_history_v215" / (day + ".json")
            path.parent.mkdir(parents=True)
            first = {"schema": "BOAT_EDGE_V215_DIAGNOSTIC_HISTORY_V1",
                     "day_jst": day, "observations": {}}
            raw = json.dumps(first).encode()
            path.write_bytes(raw)
            checker = lambda *_: ("UNUSED", None)
            a = MOD.gate1c_first_git_summary(root, day, now, verify=checker)
            self.assertEqual(a["observation_history_status"], "VERIFIED")
            self.assertEqual(a["observation_history_sha256"], hashlib.sha256(raw).hexdigest())
            self.assertFalse(a["acceptance_99_percent_proven"])
            first["observations"]["20261021-01-01"] = {
                "deadline": "15:30", "reason": "snapshot_missing"}
            changed = json.dumps(first).encode()
            path.write_bytes(changed)
            b = MOD.gate1c_first_git_summary(root, day, now, verify=checker)
            self.assertEqual(b["observation_history_sha256"], hashlib.sha256(changed).hexdigest())
            self.assertNotEqual(a["observation_history_sha256"], b["observation_history_sha256"])
            path.unlink()
            c = MOD.gate1c_first_git_summary(root, day, now, verify=checker)
            self.assertEqual(c["observation_history_status"], "MISSING")
            self.assertIsNone(c["observation_history_sha256"])
            self.assertFalse(c["acceptance_99_percent_proven"])


if __name__ == "__main__":
    unittest.main()
