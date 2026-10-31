"""Guard selection of future-only PRE_RESULT race states for read-only audits."""
import importlib.util
import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "scripts" / "fresh_upcoming_state_targets.py"
spec = importlib.util.spec_from_file_location("fresh_upcoming_state_targets", SRC)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
JST = timezone(timedelta(hours=9))

class TargetSelectionTests(unittest.TestCase):
    def test_future_only_and_pre_result_only(self):
        now = datetime(2026, 10, 26, 15, 0, tzinfo=JST)
        with tempfile.TemporaryDirectory() as root:
            for suffix, minutes, phase, seen in [
                ("01-01", 20, "PRE_RESULT", False),
                ("01-02", -1, "PRE_RESULT", False),
                ("01-03", 50, "PRE_RESULT", False),
                ("01-04", 10, "RESULT", False),
                ("01-05", 15, "PRE_RESULT", True),
            ]:
                cutoff = (now + timedelta(minutes=minutes)).strftime("%H:%M")
                state = {"meta": {"deadline": cutoff, "phase": phase, "results_seen": seen},
                         "source_audit": {"stt": {"status": "missing",
                             "observed_at": "2026-10-26T14:30:00+09:00"}}}
                (Path(root) / ("20261026-" + suffix + ".json")).write_text(json.dumps(state))
            out = mod.select(root, now, minutes=45)
        self.assertEqual([x["race_key"] for x in out], ["20261026-01-01"])
        self.assertEqual(out[0]["preview_missing_roles"], ["stt", "tkz", "sui", "original_exhibition"])
        self.assertEqual(out[0]["preview_observations_older_than_15m"][0]["role"], "stt")

if __name__ == "__main__":
    unittest.main()
