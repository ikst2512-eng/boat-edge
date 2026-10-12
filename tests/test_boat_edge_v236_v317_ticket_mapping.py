"""V317 synthetic boat-number vs course distinction tests."""
import math
import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "scripts"))
from boat_edge_v307_pl120_research import rank_120
from boat_edge_v317_ticket_mapper import map_course_mass_to_boat_tickets


class V317TicketMapping(unittest.TestCase):
    def test_permuted_entry_changes_ticket_head_not_course_head(self):
        ranked = rank_120({1: 10, 2: 1, 3: 1, 4: 1, 5: 1, 6: 1})
        courses = {1: 2, 2: 1, 3: 3, 4: 4, 5: 5, 6: 6}
        result = map_course_mass_to_boat_tickets(
            ranked, courses, "START_EXHIBITION_PROVISIONAL")
        self.assertTrue(ranked[0][0].startswith("1-"))
        self.assertTrue(result["top10_boat"][0].startswith("2-"))
        self.assertTrue(all(ticket.startswith("2-") for ticket in result["top10_boat"]))
        self.assertAlmostEqual(result["head_mass_boat"]["2"], 10 / 15)
        self.assertEqual(len(result["ranked_120_boat"]), 120)
        self.assertEqual(len(set(t["boat_combo"] for t in result["ranked_120_boat"])), 120)
        self.assertAlmostEqual(sum(t["relative_model_mass"]
                                   for t in result["ranked_120_boat"]), 1.0)
        self.assertTrue(result["entry_is_provisional"])
        self.assertFalse(result["actual_entry_independently_authenticated"])
        self.assertFalse(result["wagers_authorized"])
        self.assertFalse(result["scoring_authorized"])

    def test_no_change_entry_preserves_ticket_course_labels(self):
        ranked = rank_120({i: i for i in range(1, 7)})
        result = map_course_mass_to_boat_tickets(
            ranked, {i: i for i in range(1, 7)},
            "ACTUAL_ENTRY_ASSERTED_NOT_AUTHENTICATED")
        self.assertEqual(result["top10_boat"], [course for course, _ in ranked[:10]])
        self.assertFalse(result["entry_is_provisional"])
        self.assertFalse(result["actual_entry_independently_authenticated"])

    def test_rejects_incomplete_duplicate_and_unverified_mass(self):
        ranked = rank_120({i: i for i in range(1, 7)})
        courses = {i: i for i in range(1, 7)}
        for bad in ({1: 1}, {**courses, 2: 1}, {**courses, 6: True}):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                map_course_mass_to_boat_tickets(
                    ranked, bad, "START_EXHIBITION_PROVISIONAL")
        for bad in (
            ranked[:119], ranked[:-1] + [ranked[0]],
            ranked[:-1] + [("1-1-2", 0.1)],
            ranked[:-1] + [("1-2-3", math.nan)],
        ):
            with self.subTest(length=len(bad)), self.assertRaises(ValueError):
                map_course_mass_to_boat_tickets(
                    bad, courses, "START_EXHIBITION_PROVISIONAL")
        with self.assertRaises(ValueError):
            map_course_mass_to_boat_tickets(ranked, courses, "ACTUAL_VERIFIED")

    def test_v312_and_v308_integration(self):
        from boat_edge_v308_frozen_pl120_pipeline import build_report
        record = {
            "race_key": "SYNTHETIC-01",
            "deadline_jst": "2026-10-13T12:00:00+09:00",
            "frozen_at_jst": "2026-10-13T11:50:00+09:00",
            "source_sha256": "a" * 64,
            "source_verified": True,
            "actual_course_by_boat": {
                "1": 2, "2": 1, "3": 3, "4": 4, "5": 5, "6": 6,
            },
            "strength_by_boat": {
                "1": 1, "2": 10, "3": 1, "4": 1, "5": 1, "6": 1,
            },
        }
        report = build_report(record)
        self.assertTrue(report["top10"][0].startswith("1-"))
        self.assertTrue(report["boat_ticket_research_only"]["top10_boat"][0].startswith("2-"))
        self.assertFalse(report["actual_course_verified"])
        self.assertFalse(report["source_authentication_independent"])
        self.assertFalse(report["boat_ticket_research_only"]["wagers_authorized"])


if __name__ == "__main__":
    unittest.main()
