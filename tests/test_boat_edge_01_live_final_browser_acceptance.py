"""01 synthetic browser log gate: navigation alone is not saved TopK proof."""
import json
from pathlib import Path
import tempfile
import unittest

from scripts.boat_edge_01_live_final_browser_acceptance import (
    GateError, PAGES, CERTIFIED, verify_browser_log, verify_both,
)


def report(engine, race="20261014-15-10", status=CERTIFIED):
    return {
        "browser": engine, "target": PAGES,
        "live_topk": {
            "status": status, "race": race,
            "verified_site_final": True,
            "displayed_matches_saved_selected_mode": True,
            "saved_prediction": {"first_git_commit_verified": False},
        },
        "physical_iphone_safari_verified": False,
        "result_requests_allowed": 0,
        "formal_fresh_modified": False,
        "page_errors": [],
    }


class SavedFinalPagesGate(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def make(self, name, data):
        path = self.root / name
        path.write_text("diagnostic\nBOAT_EDGE_03_REAL_BROWSER_PASS " +
                        json.dumps(data, ensure_ascii=False) + "\n",
                        encoding="utf8")
        return path

    def test_actual_two_engines_saved_sha_parity_for_same_race(self):
        chromium = self.make("chromium", report("chromium"))
        webkit = self.make("webkit", report("webkit"))
        self.assertEqual(verify_both(chromium, webkit), "20261014-15-10")

    def test_stopped_but_navigation_pass_never_certifies(self):
        stopped = report("chromium", status="NOT_CERTIFIED_ALL_ELIGIBLE_SOURCE_STOPPED")
        with self.assertRaisesRegex(GateError, "NOT_CERTIFIED"):
            verify_browser_log(self.make("stopped", stopped), "chromium")
        reference = report("chromium", status="VERIFIED_TOP3_TOP5_TOP10_SOURCE_ORDER")
        with self.assertRaisesRegex(GateError, "NOT_CERTIFIED"):
            verify_browser_log(self.make("reference", reference), "chromium")

    def test_different_races_dont_certify_cross_engine(self):
        chromium = self.make("c", report("chromium"))
        webkit = self.make("w", report("webkit", race="20261014-20-07"))
        with self.assertRaisesRegex(GateError, "DIFFERENT_SAVED_FINAL_RACES"):
            verify_both(chromium, webkit)

    def test_missing_or_untrusted_and_outcome_access_never_passes(self):
        with self.assertRaisesRegex(GateError, "LOG_MISSING"):
            verify_browser_log(self.root / "absent", "webkit")
        data = report("webkit")
        for change in (
            {"physical_iphone_safari_verified": True},
            {"result_requests_allowed": 1},
            {"formal_fresh_modified": True},
            {"page_errors": ["uncaught exception"]},
            {"target": "https://example.invalid/boat-edge"},
        ):
            tampered = {**data, **change}
            with self.assertRaisesRegex(GateError, "NOT_CERTIFIED"):
                verify_browser_log(self.make("bad", tampered), "webkit")

    def test_claimed_immutable_sha_parity_must_really_be_true(self):
        bad = report("webkit")
        bad["live_topk"]["displayed_matches_saved_selected_mode"] = False
        with self.assertRaisesRegex(GateError, "NOT_CERTIFIED"):
            verify_browser_log(self.make("badmode", bad), "webkit")


if __name__ == "__main__":
    unittest.main()
