#!/usr/bin/env python3
"""Gate 1C: keep source-ready misses separate from earlier V215 source gaps."""
import json
from datetime import datetime, timezone
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import boat_edge_v220_site_ops as mod

DAY = "20261016"
KEY = "20261016-02-01"

def write(root, name, obj):
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj), encoding="utf-8")

class FirstGitSourceReadyMissingPrediction(unittest.TestCase):
    def fixture(self, root):
        write(root, f"data/site_ops_v220/gate1c_source_ready/{KEY}.json", {
            "race_key": KEY,
            "deadline_jst": "10:47",
            "deadline_at": "2026-10-16T01:47:00+00:00",
            "observed_at": "2026-10-16T01:41:39+00:00",
        })
        write(root, f"data/site_paper_sim/readiness_history_v215/{DAY}.json", {
            "schema": "BOAT_EDGE_V215_DIAGNOSTIC_HISTORY_V1",
            "day_jst": DAY,
            "observations": {KEY: {
                "race_key": KEY,
                "first_seen_at": "2026-10-16T01:32:48+00:00",
                "last_seen_at": "2026-10-16T01:41:39+00:00",
                "reason": "snapshot_missing",
                "source_gaps": [],
                "source_gaps_seen": ["beforeinfo_not_ok", "race_card_stale", "scratch_missing_or_blocked"],
            }},
        })

    def test_proven_source_ready_missing_freeze_is_not_labeled_source_failure(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            self.fixture(root)
            with patch.object(mod, "gate1c_source_receipt_first_git_proof", return_value=("PASS", "commit")):
                result = mod.gate1c_source_receipt_summary(
                    root, DAY, datetime(2026, 10, 16, 2, 0, tzinfo=timezone.utc),
                    prediction_verify=lambda *_: ("PASS", "commit"))
            self.assertEqual(result["source_ready_first_git_proven"], 1)
            self.assertEqual(result["source_ready_without_proven_prediction"], 1)
            self.assertEqual(result["source_ready_missing_prediction_keys"], [KEY])
            item = result["source_ready_missing_prediction_diagnostics"][0]
            self.assertEqual(item["classification"], "FIRST_GIT_SOURCE_READY_PREDICTION_NOT_PROVEN")
            self.assertEqual(item["prediction_verification_reason"], "snapshot_or_audit_missing")
            self.assertFalse(item["snapshot_file_exists"])
            self.assertEqual(item["v215_latest_source_gaps"], [])
            self.assertIn("race_card_stale", item["v215_source_gaps_ever_seen"])
            self.assertEqual(item["source_ready_observed_at"], "2026-10-16T01:41:39+00:00")
            self.assertEqual(item["writer_execution_cause"], "ACTIONS_HISTORY_REQUIRED")
            self.assertIsNone(result["eligible_save_rate_percent"])
            self.assertFalse(result["acceptance_99_percent_proven"])

    def test_unverified_receipt_never_gets_false_positive(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            self.fixture(root)
            with patch.object(mod, "gate1c_source_receipt_first_git_proof",
                              return_value=("receipt_first_git_commit_invalid", None)):
                result = mod.gate1c_source_receipt_summary(
                    root, DAY, datetime(2026, 10, 16, 2, 0, tzinfo=timezone.utc))
            self.assertEqual(result["source_ready_first_git_proven"], 0)
            self.assertEqual(result["source_ready_missing_prediction_diagnostics"], [])
            self.assertEqual(result["source_ready_without_proven_prediction"], 0)
            self.assertFalse(result["acceptance_99_percent_proven"])

if __name__ == "__main__":
    unittest.main()
