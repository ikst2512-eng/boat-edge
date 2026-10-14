"""Synthetic safeguards for preserving remote scratch evidence on collector rebase."""
from datetime import datetime, timedelta, timezone
import unittest

from scripts.boat_edge_v01_scratch_rebase_guard import safe_remote_scratch

NOW = datetime(2026, 10, 14, 17, 38, tzinfo=timezone(timedelta(hours=9)))
PATH = "data/site_scratches_v182/20261014-20-06.json"


def evidence(blocked=True, checked="17:36:00", complete=False):
    return {
        "schema_version": "boat-edge-v182-scratch-evidence-v1",
        "race_key": "20261014-20-06",
        "source_date": "20261014",
        "checked_at": "2026-10-14T" + checked + "+09:00",
        "blocked": blocked,
        "reason": None,
        "suspect_lanes": [],
        "official_raw_flags": [],
        "race_card_source_status": "ok",
        "official_beforeinfo_source_status": "ok",
        "official_beforeinfo_six_boat_complete": complete,
    }


class CollectorScratchConflictTest(unittest.TestCase):
    def test_remote_blocked_preserved(self):
        self.assertTrue(safe_remote_scratch(
            PATH, evidence(), evidence(False, "17:37:00", True), NOW))

    def test_both_green_when_source_complete(self):
        self.assertTrue(safe_remote_scratch(
            PATH, evidence(False), evidence(False, "17:37:00", True), NOW))

    def test_local_withdrawal_must_not_be_suppressed(self):
        remote = evidence(False)
        local = evidence(True, "17:37:00")
        local["reason"] = "2号艇 欠場"
        self.assertFalse(safe_remote_scratch(PATH, remote, local, NOW))

    def test_green_requires_complete_official_beforeinfo(self):
        self.assertFalse(safe_remote_scratch(
            PATH, evidence(False), evidence(False, "17:37:00", False), NOW))

    def test_bad_race_key_and_future_checked_at_refused(self):
        self.assertFalse(safe_remote_scratch(
            PATH.replace("20261014", "20261013"),
            evidence(), evidence(False, "17:37:00", True), NOW))
        future = evidence()
        future["checked_at"] = "2026-10-14T19:00:00+09:00"
        self.assertFalse(safe_remote_scratch(
            PATH, future, evidence(False, "17:37:00", True), NOW))


if __name__ == "__main__":
    unittest.main()
