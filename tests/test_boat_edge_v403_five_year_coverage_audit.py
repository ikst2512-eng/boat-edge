"""Fixture-only V403 coverage checks; never accesses any results source."""
import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from boat_edge_v403_five_year_coverage_audit import audit, MODEL


def report(day="2026-09-30", venue="01", included=1, excluded=0):
    return {
        "schema": "BOAT_EDGE_V402_OFFLINE_B_K_RECONCILIATION_RESEARCH_V1",
        "source_day": day,
        "k_normalized_sha256": "a" * 64,
        "b_original_sha256": "b" * 64,
        "b_staged_sha256": "c" * 64,
        "b_program_races_supplied": included + excluded,
        "reconciled_six_boat_races": included,
        "excluded_with_explicit_reason": excluded,
        "by_venue": {venue: {"b_program_races": included + excluded,
                             "k_complete_races": included,
                             "excluded_races": excluded}},
        "b_k_staged_race_universe_reconciled": True,
        "b_program_pre_first_deadline_capture_claim": False,
        "b_program_historic_capture_independently_authenticated": False,
        "k_post_deadline_publication_times_independently_authenticated": False,
        "national_daily_coverage_independently_verified": False,
        "license_independently_verified": False,
        "formal_fresh_read": False,
        "results_downloaded_by_this_script": False,
        "research_only": True,
        "trained_model_created": False,
        "accuracy_improvement_proven": False,
        "production_model_changed": False,
        "model_promotion_authorized": False,
        "wagers_authorized": False,
    }


class CoverageFixtureTests(unittest.TestCase):
    def test_empty_reports_do_not_claim_coverage(self):
        result = audit([])
        self.assertEqual(result["schema"], MODEL)
        self.assertEqual(result["calendar_days"], 1826)
        self.assertEqual(result["days_without_verified_v402_reports"], 1826)
        self.assertFalse(result["calendar_coverage_complete"])
        self.assertFalse(result["historical_race_coverage_independently_verified"])
        self.assertFalse(result["trained_model_created"])
        self.assertEqual(result["report_lineage"], [])

    def test_one_report_nothing_inferred_about_unseen_days(self):
        result = audit([report()])
        self.assertEqual(result["days_with_v402_reports"], 1)
        self.assertEqual(result["days_without_verified_v402_reports"], 1825)
        self.assertEqual(result["unknown_or_unsubmitted_calendar_ranges"],
                         [{"from":"2021-10-01", "through":"2026-09-29", "days":1825}])
        self.assertEqual(result["venue_counts"]["01"]["reported_race_days"], 1)
        self.assertEqual(result["venue_counts"]["02"]["reported_race_days"], 0)

    def test_year_and_venue_grouping(self):
        result = audit([report("2021-10-01","01",2,1),
                        report("2026-09-30","24",1,0)])
        self.assertEqual(result["annual_counts"]["2021"]["program_races"], 3)
        self.assertEqual(result["annual_counts"]["2026"]["complete_races"], 1)
        self.assertEqual(result["venue_counts"]["01"]["excluded_races"], 1)
        self.assertEqual(result["venue_counts"]["24"]["program_races"], 1)
        self.assertEqual(sum(x["days"] for x in result["unknown_or_unsubmitted_calendar_ranges"]),1824)

    def test_sorted_order_independent(self):
        a, b = report("2026-09-30"), report("2021-10-01","24")
        self.assertEqual(audit([a,b]),audit([b,a]))

    def test_duplicate_day_rejected(self):
        with self.assertRaisesRegex(ValueError, "DUPLICATE_DAY_REPORT"):
            audit([report(),report("2026-09-30","02")])

    def test_protected_october_day_rejected(self):
        with self.assertRaisesRegex(ValueError, "PROTECTED_OR_OUTSIDE"):
            audit([report("2026-10-01")])

    def test_pre_window_day_rejected(self):
        with self.assertRaisesRegex(ValueError, "PROTECTED_OR_OUTSIDE"):
            audit([report("2021-09-30")])

    def test_ill_formed_day_rejected(self):
        with self.assertRaisesRegex(ValueError, "V402_DATE_INVALID"):
            audit([report("n/a")])

    def test_invalid_total_rejected(self):
        x=report()
        x["b_program_races_supplied"]=3
        with self.assertRaisesRegex(ValueError, "V402_RACE_COUNTS_INCONSISTENT"):
            audit([x])

    def test_tampered_venue_total_rejected(self):
        x=report()
        x["by_venue"]["01"]["k_complete_races"]=2
        with self.assertRaisesRegex(ValueError, "V402_VENUE_COUNTS_INCONSISTENT"):
            audit([x])

    def test_venue_sum_mismatch_rejected(self):
        x=report()
        x["by_venue"]["02"]={"b_program_races":1,"k_complete_races":1,"excluded_races":0}
        with self.assertRaisesRegex(ValueError, "V402_VENUE_TOTALS_MISMATCH"):
            audit([x])

    def test_illegal_venue_rejected(self):
        with self.assertRaisesRegex(ValueError, "V402_VENUE_BREAKDOWN_INVALID"):
            audit([report(venue="25")])

    def test_sha_mismatch_rejected(self):
        x=report()
        x["b_staged_sha256"]="fake"
        with self.assertRaisesRegex(ValueError, "V402_DIGEST_INVALID"):
            audit([x])

    def test_research_promotion_flag_rejected(self):
        x=report()
        x["model_promotion_authorized"]=True
        with self.assertRaisesRegex(ValueError, "V402_RESEARCH_ISOLATION_REQUIRED"):
            audit([x])

    def test_missing_isolation_flag_rejected(self):
        x=report()
        del x["formal_fresh_read"]
        with self.assertRaisesRegex(ValueError, "V402_RESEARCH_ISOLATION_REQUIRED"):
            audit([x])

    def test_missing_venue_breakdown_rejected(self):
        x=report()
        del x["by_venue"]
        with self.assertRaisesRegex(ValueError, "V402_VENUE_BREAKDOWN_MISSING"):
            audit([x])

    def test_partial_unknown_day_is_not_fake_norace_day(self):
        res=audit([report("2026-09-29"),report("2026-09-30")])
        self.assertEqual(res["days_without_verified_v402_reports"],1824)
        self.assertFalse(res["venue_schedule_independently_verified"])

    def test_negative_and_boolean_counts_rejected(self):
        for value in (-1, True, 1.2):
            x=report()
            x["excluded_with_explicit_reason"]=value
            with self.assertRaisesRegex(ValueError, "V402_INVALID_RACE_TOTALS"):
                audit([x])

    def test_reconciliation_not_proven_rejected(self):
        x=report()
        x["b_k_staged_race_universe_reconciled"]=False
        with self.assertRaisesRegex(ValueError, "V402_RACE_UNIVERSE_NOT_RECONCILED"):
            audit([x])

    def test_empty_daily_race_cannot_fake_covered(self):
        x=report(included=0,excluded=0)
        with self.assertRaisesRegex(ValueError, "V402_RACE_COUNTS_INCONSISTENT"):
            audit([x])


if __name__ == "__main__":
    unittest.main()
