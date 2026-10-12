"""V327 V318 malformed ticket safety regression."""
import pathlib
import sys
import unittest
from datetime import datetime, timezone, timedelta

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "scripts"))
from boat_edge_v318_shadow_freeze import build_freeze


class V327MalformedTickets(unittest.TestCase):
    def test_unhashable_ticket_fails_closed_as_value_error(self):
        key = "20261013-22-12"
        report = {
            "ready_for_research_review": True,
            "bundle": {"race_key": key, "deadline_jst": "2026-10-13T16:40:00+09:00"},
            "evidence_audit": {"all_three_document_bundles_consistent": True},
        }
        candidate = {
            "race_key": key, "production_eligible": False,
            "scoring_authorized": False, "calibrated": False,
            "improvement_proven": False,
            "modes": {"national_only": {
                "top10_boat_research_only": [["1", "2", "3"]] + [
                    f"1-2-{i}" for i in range(9)
                ]
            }},
        }
        now = datetime(2026, 10, 13, 16, 30, tzinfo=timezone(timedelta(hours=9)))
        with self.assertRaisesRegex(ValueError, "INVALID_TICKET"):
            build_freeze(report, candidate, now)


if __name__ == "__main__":
    unittest.main()
