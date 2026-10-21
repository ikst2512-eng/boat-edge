#!/usr/bin/env python3
"""Offline validation for independent original exhibition coverage helper."""
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from boat_edge_original_exhibition_coverage import assess_original_exhibition, classify_fetch_failure, retry_delay_seconds, assess_official_beforeinfo


def six():
    return [{"boat": n, "lap": "36.2", "turn": "5.6", "straight": "7.4"}
            for n in range(1, 7)]


class TestOriginalExhibitionCoverage(unittest.TestCase):
    def test_official_beforeinfo_not_confused_with_original(self):
        parsed = {"racers": [{"lane": n, "exhibition_time": 6.8} for n in range(1, 7)],
                  "start_exhibition": [{"lane": n, "st": ".12"} for n in range(1, 7)]}
        out = assess_official_beforeinfo(parsed)
        self.assertEqual(out["official_beforeinfo_status"], "COMPLETE")
        self.assertEqual(out["original_exhibition_status"], "NOT_VERIFIED")

    def test_official_beforeinfo_partial(self):
        out = assess_official_beforeinfo({"racers": [], "start_exhibition": []})
        self.assertEqual(out["official_beforeinfo_status"], "PARTIAL_SIX_BOATS")
        self.assertEqual(out["original_exhibition_status"], "NOT_VERIFIED")

    def test_complete(self):
        self.assertEqual(assess_original_exhibition(six())["status"], "COMPLETE_SIX_BOATS")

    def test_unpublished(self):
        self.assertEqual(assess_original_exhibition(None)["status"], "NOT_YET_PUBLISHED")

    def test_partial(self):
        self.assertEqual(assess_original_exhibition(six()[:5])["status"], "PARTIAL_SIX_BOATS")

    def test_duplicate_lane(self):
        rows = six()
        rows[-1]["boat"] = 5
        self.assertEqual(assess_original_exhibition(rows)["status"], "PARTIAL_SIX_BOATS")

    def test_missing_not_zero(self):
        rows = six()
        rows[2]["turn"] = "─"
        report = assess_original_exhibition(rows)
        self.assertIn("NOT_MEASURED", report["status"])
        self.assertEqual(report["missing"]["3"], ["turn"])

    def test_bad_value(self):
        rows = six()
        rows[0]["lap"] = "broken"
        self.assertEqual(assess_original_exhibition(rows)["status"], "PARSE_FAILED")

    def test_deadline(self):
        a = datetime(2026, 10, 21, 14, 15, tzinfo=timezone.utc)
        self.assertEqual(
            assess_original_exhibition(six(), fetched_at=a, deadline=a)["status"],
            "STALE_AFTER_DEADLINE",
        )

    def test_string_boat_ids(self):
        rows = six()
        for row in rows:
            row["boat"] = str(row["boat"])
        self.assertEqual(assess_original_exhibition(rows)["status"], "COMPLETE_SIX_BOATS")

    def test_retry_stops_at_deadline_and_on_permission(self):
        self.assertEqual(retry_delay_seconds(0, "HTTP_UNAVAILABLE", remaining_seconds=20), 3)
        self.assertIsNone(retry_delay_seconds(0, "HTTP_UNAVAILABLE", remaining_seconds=3))
        self.assertIsNone(retry_delay_seconds(0, "ACCESS_RESTRICTED", remaining_seconds=20))

    def test_invalid_lane_type(self):
        rows = six()
        rows[0]["boat"] = True
        self.assertEqual(assess_original_exhibition(rows)["status"], "PARTIAL_SIX_BOATS")

    def test_invalid_missing_cell_container(self):
        rows = six()
        rows[0]["lap"] = []
        self.assertEqual(assess_original_exhibition(rows)["status"], "PARSE_FAILED")

    def test_404_no_unbounded_retry(self):
        err = type("Error", (), {"code": 404})()
        self.assertFalse(classify_fetch_failure(err)["retryable"])
        self.assertIsNone(retry_delay_seconds(0, "NOT_YET_PUBLISHED_OR_BAD_URL", remaining_seconds=100))

    def test_overflow_is_not_valid_measurement(self):
        rows = six()
        rows[0]["lap"] = "9" * 400
        self.assertEqual(assess_original_exhibition(rows)["status"], "PARSE_FAILED")

    def test_access_restricted(self):
        err = type("Error", (), {"code": 403})()
        self.assertEqual(classify_fetch_failure(err)["status"], "ACCESS_RESTRICTED")


if __name__ == "__main__":
    unittest.main()
