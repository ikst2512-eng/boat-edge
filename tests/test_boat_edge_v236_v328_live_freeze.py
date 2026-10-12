"""V328 live-only integration runner blocks late or result-bearing races."""
import json
import hashlib
import pathlib
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "scripts"))
from boat_edge_v328_live_research_freeze import live_research_freeze

JST = timezone(timedelta(hours=9))
KEY = "20261013-22-12"


def write_race(root, **overrides):
    meta = {
        "date": "2026-10-13", "deadline": "16:40",
        "updated_at": "2026-10-13T16:20:00+09:00",
        "phase": "PRE_RESULT", "results_seen": False,
        "unlock": False, "scoring": False,
    }
    meta.update(overrides)
    race = {"race_key": KEY, "meta": meta,
            "source_audit": {
                "race_card": {"status": "ok", "fetched_at": "2026-10-13T16:18:00+09:00"},
                "beforeinfo": {"status": "ok", "fetched_at": "2026-10-13T16:19:00+09:00"},
            }}
    folder = root / "data/races"
    folder.mkdir(parents=True)
    (folder / (KEY + ".json")).write_text(json.dumps(race))


class V328LiveOnly(unittest.TestCase):
    def test_immutable_candidate_digest_includes_race_source_sha(self):
        from boat_edge_v318_shadow_freeze import canonical
        candidate = {"race_key": KEY, "modes": {}, "race_source_sha256": "a" * 64}
        first = hashlib.sha256(canonical(candidate)).hexdigest()
        candidate["race_source_sha256"] = "b" * 64
        self.assertNotEqual(first, hashlib.sha256(canonical(candidate)).hexdigest())

    def test_late_clock_rejected_without_write(self):
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            write_race(root)
            with self.assertRaisesRegex(ValueError, "LIVE_WINDOW_CLOSED"):
                live_research_freeze(root, KEY, datetime(2026, 10, 13, 16, 41, tzinfo=JST))
            self.assertFalse((root / "data/research_shadow_v318").exists())

    def test_results_flag_rejected_before_any_candidate(self):
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            write_race(root, results_seen=True)
            with self.assertRaisesRegex(ValueError, "RESULT_OR_UNLOCK"):
                live_research_freeze(root, KEY, datetime(2026, 10, 13, 16, 30, tzinfo=JST))

    def test_postdeadline_source_timestamp_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            write_race(root, updated_at="2026-10-13T16:45:00+09:00")
            with self.assertRaisesRegex(ValueError, "RACE_FILE_TIMESTAMP_NOT_PREDEADLINE"):
                live_research_freeze(root, KEY, datetime(2026, 10, 13, 16, 30, tzinfo=JST))

    def test_missing_racer_inputs_not_imputed(self):
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            write_race(root)
            with self.assertRaises(ValueError):
                live_research_freeze(root, KEY, datetime(2026, 10, 13, 16, 30, tzinfo=JST))
            self.assertFalse((root / "data/research_shadow_v318").exists())


if __name__ == "__main__":
    unittest.main()
