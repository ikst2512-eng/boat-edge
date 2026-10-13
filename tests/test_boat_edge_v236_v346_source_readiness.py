"""V346 safe selection-time diagnostics; synthetic current-day PRE_RESULT only."""
from datetime import timedelta
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from boat_edge_v346_source_readiness import scan_preflight
from boat_edge_v334_live_batch_runner import run
from test_boat_edge_v236_v334_live_batch import NOW, prepare, fake_fetch

KEY = "20261013-22-12"


def inspect(root):
    path = root / "data/races" / (KEY + ".json")
    raw = path.read_bytes()
    return scan_preflight(json.loads(raw), raw, NOW)


def edit(root, fn):
    path = root / "data/races" / (KEY + ".json")
    doc = json.loads(path.read_bytes())
    fn(doc)
    path.write_text(json.dumps(doc), encoding="utf-8")


class V346SourceReadiness(unittest.TestCase):
    def test_healthy_synthetic_card_reports_readiness_not_certification(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            prepare(root)
            out = inspect(root)
            self.assertEqual(out["issues"], [])
            self.assertEqual(out["start_exhibition_explicit_course_lanes"], list(range(1, 7)))
            self.assertEqual(out["feature_complete_boats"], list(range(1, 7)))
            self.assertFalse(out["preflight_can_authorize_freeze"])
            self.assertFalse(out["results_read"])
            self.assertFalse(out["actual_entry_independently_verified"])
            self.assertTrue(out["selection_snapshot_may_differ_from_freeze_input"])
            raw = (root / "data/races" / (KEY + ".json")).read_bytes()
            self.assertEqual(out["selection_race_input_sha256"], hashlib.sha256(raw).hexdigest())

    def test_missing_course_is_not_silent_identity_fallback(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            prepare(root)
            edit(root, lambda r: [x.pop("course") for x in r["beforeinfo"]["start_exhibition"]])
            result = run(root, capture=True, clock=lambda: NOW,
                         fetcher=lambda url: self.fail("NO_UPSTREAM_FETCH_ON_BAD_COURSE"))
            self.assertEqual(result["completed_count"], 0)
            self.assertEqual(result["run_diagnostic"], "ELIGIBLE_BUT_NO_FREEZE_COMPLETED")
            f = result["failures"][0]
            self.assertEqual(f["reason"], "PREDEADLINE_SOURCE_AND_EXHIBITION_GATE_NOT_MET")
            scan = f["selection_scan"]
            self.assertFalse(scan["start_exhibition_provisional_permutation_recorded"])
            self.assertEqual(scan["start_exhibition_explicit_course_lanes"], [])
            self.assertIn("START_EXHIBITION_COURSE_MISSING_OR_INVALID", scan["issues"])
            self.assertFalse((root / "data/research_local_v332").exists())

    def test_stale_card_and_beforeinfo_are_distinct(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            prepare(root)
            def change(r):
                for name in ("race_card", "beforeinfo"):
                    r["source_audit"][name]["fetched_at"] = "2026-10-13T16:00:00+09:00"
            edit(root, change)
            out = inspect(root)
            self.assertIn("SOURCE_SCAN_STALE:race_card", out["issues"])
            self.assertIn("SOURCE_SCAN_STALE:beforeinfo", out["issues"])
            result = run(root, capture=True, clock=lambda: NOW,
                         fetcher=lambda url: self.fail("NO_FETCH_STALE"))
            self.assertEqual(result["completed_count"], 0)
            self.assertIn("SOURCE_TOO_STALE_FOR_FINAL_WINDOW", result["failures"][0]["reason"])
            self.assertIn("SOURCE_SCAN_STALE:race_card",
                          result["failures"][0]["selection_scan"]["issues"])

    def test_status_and_missing_features_reported_without_imputation(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            prepare(root)
            def change(r):
                r["source_audit"]["beforeinfo"]["status"] = "published_wait"
                r["racers"][5]["avg_st"] = None
            edit(root, change)
            out = inspect(root)
            self.assertIn("BEFOREINFO_NOT_PREDEADLINE_PROVEN", out["issues"])
            self.assertIn("SOURCE_NOT_OK:beforeinfo", out["issues"])
            self.assertIn("SIX_RACER_FEATURES_INCOMPLETE", out["issues"])
            self.assertEqual(out["feature_complete_boats"], [1, 2, 3, 4, 5])
            self.assertFalse(out["source_bytes_independently_authenticated"])

    def test_bad_flags_and_closed_time_rejected_without_lookups(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            prepare(root)
            raw = (root / "data/races" / (KEY + ".json")).read_bytes()
            original = json.loads(raw)
            for name in ("results_seen", "unlock", "scoring"):
                doc = json.loads(raw)
                doc["meta"][name] = True
                with self.assertRaisesRegex(ValueError, "SCAN_PRE_RESULT_ONLY"):
                    scan_preflight(doc, raw, NOW)
            forbidden = json.loads(raw)
            forbidden["results"] = {"not_read": True}
            with self.assertRaisesRegex(ValueError, "SCAN_PRE_RESULT_ONLY"):
                scan_preflight(forbidden, raw, NOW)
            with self.assertRaisesRegex(ValueError, "SCAN_CLOSED_RACE"):
                scan_preflight(original, raw, NOW + timedelta(minutes=15))
            with self.assertRaisesRegex(ValueError, "SCAN_AWARE_CLOCK_REQUIRED"):
                scan_preflight(original, raw, NOW.replace(tzinfo=None))
            self.assertFalse((root / "data/research_local_v332").exists())


if __name__ == "__main__":
    unittest.main()
