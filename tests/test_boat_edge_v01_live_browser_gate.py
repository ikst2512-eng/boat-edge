"""Synthetic, result-unseen tests for V229 saved-final browser trigger."""
from datetime import datetime, timedelta, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

from scripts.boat_edge_v01_live_browser_gate import (
    candidates, first_git_add_proof, valid, selected_live_race,
)

JST = timezone(timedelta(hours=9))
NOW = datetime(2026, 10, 14, 19, 30, tzinfo=JST)
KEY = "20261014-15-10"
ADD = datetime(2026, 10, 14, 19, 29, 37, tzinfo=JST)


def fixture():
    tickets = [
        {"combo": combo}
        for combo in ("1-2-3", "1-2-4", "1-2-5", "1-2-6",
                      "1-3-2", "1-3-4", "1-3-5", "1-3-6",
                      "1-4-2", "1-4-3")
    ]
    s = {
        "race_key": KEY, "deadline": "19:36",
        "snapshot_window": "FINAL_15M",
        "prediction_kind": "SITE_REFERENCE_V122",
        "first_saved_at": "2026-10-14T19:29:36+09:00",
        "saved_at": "2026-10-14T19:29:36+09:00",
        "guards": {"results_seen": False, "unlock": False, "scoring": False},
        "modes": {"hit": {"tickets": tickets}},
    }
    blob = json.dumps(s, sort_keys=True).encode()
    digest = hashlib.sha256(blob).hexdigest()
    a = {"race_key": KEY, "pass": True, "latest_snapshot_sha256": digest}
    e = {
        "schema": "BOAT_EDGE_V229_ATOMIC_PRE_RESULT_SOURCE_EVIDENCE_V1",
        "scope": "SITE_REFERENCE_ONLY_NO_FORMAL_OR_RESULT_ACCESS",
        "race_key": KEY, "snapshot_sha256": digest,
        "snapshot_saved_at": s["saved_at"],
        "new_snapshot_created_this_run": True,
        "results_seen": False, "formal_fresh_unlock": False, "scoring": False,
    }
    return s, a, e, blob


class FirstAddBrowserGate(unittest.TestCase):
    def test_both_browsers_use_one_deterministic_longest_lived_proof(self):
        records = [
            {"race_key": "20261015-11-11", "deadline": "15:14"},
            {"race_key": "20261015-12-01", "deadline": "15:16"},
            {"race_key": "20261015-02-10", "deadline": "15:18"},
        ]
        self.assertEqual(selected_live_race(records), "20261015-02-10")
        self.assertEqual(selected_live_race(list(reversed(records))),
                         "20261015-02-10")
        self.assertIsNone(selected_live_race([]))
        self.assertEqual(selected_live_race([records[0]]),
                         "20261015-11-11")

    def test_first_git_add_bytes_not_current_audit_determine_browser_certification(self):
        # Only synthetic PRE_RESULT files; no result endpoints or historical
        # predictions. The first Git ADD is before the 19:36 deadline.
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            def write(relative, value):
                path = root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(json.dumps(value, sort_keys=True), encoding="utf-8")
            def git(*args, when="2026-10-14T10:29:37+00:00"):
                env = dict(os.environ, GIT_AUTHOR_DATE=when,
                           GIT_COMMITTER_DATE=when)
                return subprocess.run(["git", *args], cwd=root, env=env,
                                      capture_output=True, text=True, check=True)
            git("init", "-q")
            git("config", "user.name", "Fixture")
            git("config", "user.email", "fixture@example.invalid")
            snapshot, audit, receipt, _ = fixture()
            snap_path = f"data/site_prediction_snapshots/{KEY}.json"
            audit_path = f"data/site_prediction_audit/{KEY}.json"
            receipt_path = f"data/site_autopilot/v229_evidence/{KEY}.json"
            write(snap_path, snapshot)
            git("add", "--", snap_path)
            git("commit", "-qm", "First predeadline frozen snapshot")
            def same_sha_receipts():
                digest = hashlib.sha256((root / snap_path).read_bytes()).hexdigest()
                audit["latest_snapshot_sha256"] = digest
                receipt["snapshot_sha256"] = digest
                write(audit_path, audit)
                write(receipt_path, receipt)
            same_sha_receipts()
            write("data/formal_status.json", {
                "guards": {"results_seen": False, "unlock": False,
                           "scoring": False, "RESULT_UNLOCK_TOKEN": None},
                "formalFirst100": {"races": 0},
            })
            proof = first_git_add_proof(root, root / snap_path)
            self.assertIsNotNone(proof)
            self.assertEqual(proof[1], hashlib.sha256((root / snap_path).read_bytes()).hexdigest())
            self.assertEqual(len(candidates(root, NOW)), 1)

            # Simulate an illicit later snapshot edit with its current audit and
            # receipt both rewritten to match. This must NEVER borrow first-add.
            snapshot["selection_policy"] = "REPLACED_AFTER_FIRST_GIT_ADD"
            write(snap_path, snapshot)
            same_sha_receipts()
            git("add", "--", snap_path, audit_path, receipt_path)
            git("commit", "-qm", "Later consistent HEAD rewrite",
                when="2026-10-14T10:29:48+00:00")
            self.assertEqual(candidates(root, NOW), [])
            original = first_git_add_proof(root, root / snap_path)
            self.assertEqual(original[0], proof[0])
            self.assertEqual(original[1], proof[1])
            self.assertEqual(original[2], proof[2])

    def test_real_proven_frozen_input_triggers_before_deadline(self):
        self.assertTrue(valid(*fixture(), KEY, NOW, ADD))

    def test_subsecond_snapshot_with_same_second_git_first_add(self):
        # Reproduce the actual V229 clock precision mismatch:
        # saved_at=14:29:45.646, first Git commit=%cI 14:29:45.
        s, _, e, _ = fixture()
        s["first_saved_at"] = "2026-10-14T19:29:37.640+09:00"
        s["saved_at"] = "2026-10-14T19:29:37.646+09:00"
        blob = json.dumps(s, sort_keys=True).encode()
        digest = hashlib.sha256(blob).hexdigest()
        a = {"race_key": KEY, "pass": True,
             "latest_snapshot_sha256": digest}
        e["snapshot_saved_at"] = s["saved_at"]
        e["snapshot_sha256"] = digest
        same_second = datetime(2026, 10, 14, 19, 29, 37, tzinfo=JST)
        self.assertTrue(valid(s, a, e, blob, KEY, NOW, same_second))
        # Truly earlier Git seconds cannot borrow the snapshot evidence.
        self.assertFalse(valid(s, a, e, blob, KEY, NOW,
                               same_second - timedelta(seconds=1)))
        # The exact-source/audit SHA still cannot be substituted.
        self.assertFalse(valid(s, a, e, blob + b"changed", KEY, NOW,
                               same_second))
        self.assertFalse(valid(s, a, {**e, "snapshot_sha256": "f" * 64},
                               blob, KEY, NOW, same_second))

    def test_no_late_backfill_or_missing_git_first_add(self):
        self.assertFalse(valid(*fixture(), KEY, NOW, None))
        self.assertFalse(valid(*fixture(), KEY,
                               datetime(2026, 10, 14, 19, 36, tzinfo=JST), ADD))
        self.assertFalse(valid(*fixture(), KEY, NOW,
                               datetime(2026, 10, 14, 19, 37, tzinfo=JST)))
        self.assertFalse(valid(*fixture(), KEY,
                               datetime(2026, 10, 14, 19, 23, tzinfo=JST), ADD))

    def test_mismatched_sha_and_missing_evidence_never_triggers(self):
        s, a, e, blob = fixture()
        self.assertFalse(valid(s, a, e, blob + b"changed", KEY, NOW, ADD))
        self.assertFalse(valid(s, a, {**e, "snapshot_sha256": "f"*64},
                               blob, KEY, NOW, ADD))
        self.assertFalse(valid(s, {**a, "pass": False}, e,
                               blob, KEY, NOW, ADD))
        self.assertFalse(valid(s, a, None, blob, KEY, NOW, ADD))

    def test_frozen_source_guard_and_first_add_order(self):
        s, a, e, blob = fixture()
        s["guards"]["results_seen"] = True
        self.assertFalse(valid(s, a, e, blob, KEY, NOW, ADD))
        s, a, e, blob = fixture()
        e["new_snapshot_created_this_run"] = False
        self.assertFalse(valid(s, a, e, blob, KEY, NOW, ADD))
        s, a, e, blob = fixture()
        self.assertFalse(valid(s, a, e, blob, KEY, NOW,
                               datetime(2026, 10, 14, 19, 28, tzinfo=JST)))

    def test_only_exact_empty_v125_settlement_sentinel_is_pre_result(self):
        s, a, e, blob = fixture()
        sentinel = {"available": False, "winning_combo": None, "hit_any": None,
                    "mode_hits": {}, "payout": None}
        a["settlement"] = sentinel
        self.assertTrue(valid(s, a, e, blob, KEY, NOW, ADD))
        for bad in ({**sentinel, "available": True},
                    {**sentinel, "hit_any": False},
                    {**sentinel, "payout": 0},
                    {**sentinel, "winning_combo": "1-2-3"},
                    {**sentinel, "mode_hits": {"hit": True}},
                    {**sentinel, "extra": None},
                    {}, None):
            a["settlement"] = bad
            self.assertFalse(valid(s, a, e, blob, KEY, NOW, ADD))

    def test_post_result_audit_never_triggers_live(self):
        s, a, e, blob = fixture()
        a["settlement"] = {"available": True}
        self.assertFalse(valid(s, a, e, blob, KEY, NOW, ADD))


if __name__ == "__main__":
    unittest.main()
