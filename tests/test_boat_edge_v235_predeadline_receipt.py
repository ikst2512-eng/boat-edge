#!/usr/bin/env python3
"""No-network prospective receipt tests; never read results/formal files."""
import hashlib
import json
import os
from datetime import datetime
from pathlib import Path
import subprocess
import tempfile
import unittest

from scripts.boat_edge_v235_predeadline_receipt import JST, receipt, choose

KEY = "20261014-14-01"


def save(root, path, obj):
    target = root / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(obj, ensure_ascii=False) + "\n", encoding="utf-8")
    return target


def source(root):
    save(root, "data/today.json", {
        "date": "2026-10-14", "venues": [{"venue": "鳴門", "races": [
            {"race_key": KEY, "deadline": "08:35"}]}]})
    save(root, f"data/races/{KEY}.json", {
        "race_key": KEY, "meta": {"phase": "PRE_RESULT",
                                   "results_seen": False, "unlock": False, "scoring": False},
        "source_audit": {"race_card": {"status": "ok"},
                         "beforeinfo": {"status": "not_in_window"}}})


def frozen(root):
    snap = {
        "race_key": KEY, "schema_version": "boat-edge-server-site-final-v123",
        "snapshot_window": "FINAL_15M", "prediction_kind": "SITE_REFERENCE_V122",
        "selection_policy": "V122_SCENARIO_AWARE_PROBABILITY_FIRST",
        "first_saved_at": "2026-10-14T08:28:00+09:00",
        "saved_at": "2026-10-14T08:28:00+09:00",
        "guards": {"results_seen": False, "unlock": False, "scoring": False},
        "modes": {"hit": {"tickets": [{"combo": x} for x in (
            "1-2-3", "1-2-4", "1-2-5", "1-2-6", "1-3-2", "1-3-4",
            "1-3-5", "1-3-6", "1-4-2", "1-4-3")]}}}
    path = save(root, f"data/site_prediction_snapshots/{KEY}.json", snap)
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    save(root, f"data/site_prediction_audit/{KEY}.json", {
        "race_key": KEY, "pass": True, "latest_snapshot_sha256": digest})
    return path


class V235Proof(unittest.TestCase):
    def test_window_does_not_invent_a_prediction(self):
        with tempfile.TemporaryDirectory() as base:
            root = Path(base)
            source(root)
            early = receipt(root, datetime(2026, 10, 14, 8, 10, tzinfo=JST))
            self.assertEqual(early["status"], "BEFORE_SOURCE_WINDOW")
            self.assertFalse(early["prediction_saved_proven"])
            self.assertEqual(early["race_key"], KEY)
            active = receipt(root, datetime(2026, 10, 14, 8, 28, tzinfo=JST))
            self.assertEqual(active["status"], "SOURCE_WINDOW_NO_SNAPSHOT")
            self.assertFalse(active["prediction_saved_proven"])

    def test_1r_priority_advances_to_next_race_after_deadline(self):
        with tempfile.TemporaryDirectory() as base:
            root = Path(base)
            source(root)
            catalog = json.loads((root / "data/today.json").read_text())
            catalog["venues"][0]["races"].append({
                "race_key": "20261014-14-02", "deadline": "09:01"})
            save(root, "data/today.json", catalog)
            before = datetime(2026, 10, 14, 8, 20, tzinfo=JST)
            after = datetime(2026, 10, 14, 8, 38, tzinfo=JST)
            self.assertEqual(choose(root, before)[1], KEY)
            self.assertEqual(choose(root, after)[1], "20261014-14-02")
            self.assertEqual(choose(root, after, requested=KEY)[1], KEY)

    def test_local_only_not_a_git_commit(self):
        with tempfile.TemporaryDirectory() as base:
            root = Path(base)
            source(root)
            frozen(root)
            candidate = receipt(root, datetime(2026, 10, 14, 8, 29, tzinfo=JST))
            self.assertEqual(candidate["status"], "LOCAL_SNAPSHOT_NOT_FIRST_GIT_COMMITTED")
            self.assertFalse(candidate["prediction_saved_proven"])
            self.assertEqual(candidate["model_id"], "not_stored")
            self.assertEqual(candidate["prediction_kind"], "SITE_REFERENCE_V122")
            self.assertEqual(len(candidate["top10"]), 10)

    def test_exact_sha_first_added_commit_before_deadline(self):
        with tempfile.TemporaryDirectory() as base:
            root = Path(base)
            source(root)
            path = frozen(root)
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            subprocess.run(["git", "config", "user.name", "Test"], cwd=root, check=True)
            subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=root, check=True)
            subprocess.run(["git", "add", "data/today.json", "data/races",
                            "data/site_prediction_snapshots", "data/site_prediction_audit"],
                           cwd=root, check=True)
            env = os.environ.copy()
            env["GIT_AUTHOR_DATE"] = "2026-10-14T08:29:00+09:00"
            env["GIT_COMMITTER_DATE"] = "2026-10-14T08:29:00+09:00"
            subprocess.run(["git", "commit", "-qm", "prospective proof"], cwd=root,
                           env=env, check=True)
            result = receipt(root, datetime(2026, 10, 14, 8, 31, tzinfo=JST))
            self.assertEqual(result["status"], "SITE_FIRST_GIT_COMMIT_BEFORE_DEADLINE")
            self.assertTrue(result["prediction_saved_proven"])
            self.assertEqual(result["snapshot_sha256"], hashlib.sha256(path.read_bytes()).hexdigest())
            self.assertEqual(result["first_git_snapshot_sha256"], result["snapshot_sha256"])
            self.assertEqual(len(result["first_git_commit"]), 40)
            self.assertTrue(result["first_git_commit_at"].startswith("2026-10-14T08:29:00"))

    def test_git_first_commit_after_deadline_is_not_a_valid_save(self):
        with tempfile.TemporaryDirectory() as base:
            root = Path(base)
            source(root)
            frozen(root)
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            subprocess.run(["git", "config", "user.name", "Test"], cwd=root, check=True)
            subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=root, check=True)
            subprocess.run(["git", "add", "data/today.json", "data/races",
                            "data/site_prediction_snapshots", "data/site_prediction_audit"],
                           cwd=root, check=True)
            env = os.environ.copy()
            env["GIT_AUTHOR_DATE"] = "2026-10-14T08:36:00+09:00"
            env["GIT_COMMITTER_DATE"] = "2026-10-14T08:36:00+09:00"
            subprocess.run(["git", "commit", "-qm", "late publish not prospective"],
                           cwd=root, env=env, check=True)
            result = receipt(root, datetime(2026, 10, 14, 8, 37, tzinfo=JST))
            self.assertEqual(result["status"], "FIRST_GIT_COMMIT_NOT_SOURCE_BOUND_PREDEADLINE")
            self.assertFalse(result["prediction_saved_proven"])

    def test_audit_failure_fails_closed(self):
        with tempfile.TemporaryDirectory() as base:
            root = Path(base)
            source(root)
            frozen(root)
            save(root, f"data/site_prediction_audit/{KEY}.json", {
                "pass": True, "latest_snapshot_sha256": "0" * 64})
            result = receipt(root, datetime(2026, 10, 14, 8, 31, tzinfo=JST))
            self.assertEqual(result["status"], "SNAPSHOT_OR_V229_AUDIT_UNVERIFIED")
            self.assertFalse(result["prediction_saved_proven"])

    def test_workflow_has_0820_jst_owner_without_duplicate_writers(self):
        text = (Path(__file__).resolve().parents[1] /
                ".github/workflows/V235.yml").read_text(encoding="utf-8")
        self.assertIn("cron: '20 23 * * *'", text)
        self.assertIn("python3 scripts/boat_edge_v230_fast_lane.py --workers 8 --retry-imminent", text)
        self.assertNotIn("--priority-race-key 20261014-14-01", text)
        self.assertIn("python3 scripts/boat_edge_v232_pre_result_cohort.py", text)
        self.assertIn("python3 scripts/boat_edge_v235_predeadline_receipt.py", text)
        self.assertIn("V235_END_TO_END_SITE_PRE_RESULT_COHORT_VERIFIED", text)
        # A local predeadline snapshot is not proof of a timely first Git commit.
        self.assertIn("V235_TAKEOVER_CANDIDATE=1", text)
        self.assertIn("V235_TAKEOVER_FIRST_GIT_PROOF", text)
        self.assertIn("V235_FIRST_GIT_PROOF_REQUIRED_KEEP_V233", text)
        self.assertIn("if: ${{ !cancelled() }}", text)
        self.assertIn("env.write('V235_TAKEOVER_VERIFIED=1' + chr(10))", text)
        self.assertLess(text.index("V235_TAKEOVER_CANDIDATE=1"),
                        text.index("V235_TAKEOVER_FIRST_GIT_PROOF"))
        self.assertLess(text.index("V235_TAKEOVER_FIRST_GIT_PROOF"),
                        text.index("V235_TAKEOVER_VERIFIED=1' + chr(10)"))
        self.assertLess(text.index("V235_TAKEOVER_VERIFIED=1' + chr(10)"),
                        text.index("Disable obsolete V234 and V233"))
        self.assertIn("V235_KEEP_V233_UNTIL_NEW_PRE_RESULT_EVIDENCE_IS_COMMITTED", text)
        for unsafe in ("results_seen=true", "scoring=true", "git push --force"):
            self.assertNotIn(unsafe, text)


if __name__ == "__main__":
    unittest.main()
