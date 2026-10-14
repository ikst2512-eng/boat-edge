"""Synthetic, result-unseen tests for V229 saved-final browser trigger."""
from datetime import datetime, timedelta, timezone
import hashlib
import json
import unittest

from scripts.boat_edge_v01_live_browser_gate import valid

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
    def test_real_proven_frozen_input_triggers_before_deadline(self):
        self.assertTrue(valid(*fixture(), KEY, NOW, ADD))

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
