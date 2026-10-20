from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import json
import unittest

import boat_edge_c1_observed_audit as m

KEY = "20261020-03-11"


class C1ObservedAuditTests(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.write("data/today.json", {"date": "2026-10-20", "venues": [
            {"venue": "江戸川", "races": [{"race_key": KEY, "deadline": "15:53"},
                                      {"race_key": "20261020-03-12", "deadline": "16:20"}]}]})
        self.write("data/site_paper_sim/readiness_history_v215/20261020.json",
                   {"day_jst": "20261020", "observations": {KEY: {
                       "reason": "snapshot_missing", "last_seen_at": "2026-10-20T06:43:00+00:00",
                       "source_gaps": []}}})

    def write(self, name, data):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data), encoding="utf-8")

    def test_before_deadline_missing_is_pending_not_failure(self):
        with patch.object(m, "receipt", return_value={"prediction_saved_proven": False,
                                                       "status": "SOURCE_WINDOW_NO_SNAPSHOT"}):
            data = m.accounting(self.root, datetime(2026, 10, 20, 6, 47, tzinfo=timezone.utc))
        self.assertEqual(data["classification_counts"], {"PENDING_BEFORE_DEADLINE": 1})
        self.assertEqual(data["not_observed_count"], 1)
        self.assertFalse(data["eligible_denominator_verified"])
        self.assertFalse(data["c1_99_percent_proven"])

    def test_after_deadline_without_git_proof_is_unproven_not_eligible_failure(self):
        with patch.object(m, "receipt", return_value={"prediction_saved_proven": False,
                                                       "status": "LOCAL_SNAPSHOT_NOT_FIRST_GIT_COMMITTED"}):
            data = m.accounting(self.root, datetime(2026, 10, 20, 6, 54, tzinfo=timezone.utc))
        self.assertEqual(data["classification_counts"], {"UNPROVEN_AFTER_DEADLINE": 1})
        self.assertEqual(data["races"][0]["last_observed_reason"], "snapshot_missing")

    def test_late_readiness_history_does_not_override_proven_git_first_add(self):
        with patch.object(m, "receipt", return_value={"prediction_saved_proven": True,
                                                       "status": "SITE_FIRST_GIT_COMMIT_BEFORE_DEADLINE"}):
            data = m.accounting(self.root, datetime(2026, 10, 20, 6, 54, tzinfo=timezone.utc))
        self.assertEqual(data["classification_counts"], {"PROVEN_FIRST_GIT_BEFORE_DEADLINE": 1})
        self.assertFalse(data["c1_99_percent_proven"])

    def test_historic_day_uses_observed_deadline_but_not_eligible_denominator(self):
        self.write("data/site_paper_sim/readiness_history_v215/20261020.json",
                   {"observations": {KEY: {"deadline": "15:53",
                                             "reason": "snapshot_missing",
                                             "last_seen_at": "2026-10-20T06:43:00+00:00"}}})
        self.write("data/today.json", {"date": "2026-10-21", "venues": []})
        with patch.object(m, "archived_receipt", return_value={
            "prediction_saved_proven": True,
            "status": "ARCHIVED_FIRST_GIT_PREDEADLINE"}) as proof:
            data = m.accounting(self.root, datetime(2026, 10, 21, 1, tzinfo=timezone.utc),
                                day="20261020")
        self.assertEqual(data["classification_counts"], {"PROVEN_FIRST_GIT_BEFORE_DEADLINE": 1})
        self.assertEqual(data["deadline_source"], "HISTORICAL_V215_OBSERVATION_UNVERIFIED")
        self.assertIsNone(data["scheduled_races_catalog"])
        self.assertFalse(data["eligible_denominator_verified"])
        self.assertFalse(data["c1_99_percent_proven"])
        proof.assert_called_once()

    def test_stale_catalog_uses_historic_git_verifier_not_v235_today(self):
        # Real 2026-10-21 rollover: today.json was still dated Oct 20.
        # The same-day V235 receipt would return NO_SAME_DAY_VERIFIED_RACE_ID.
        self.write("data/site_paper_sim/readiness_history_v215/20261020.json",
                   {"observations": {KEY: {"deadline": "15:53",
                                             "reason": "snapshot_missing"}}})
        with patch.object(m, "receipt") as live, patch.object(
            m, "archived_receipt", return_value={
                "prediction_saved_proven": True,
                "status": "ARCHIVED_FIRST_GIT_PREDEADLINE",
            }) as archived:
            data = m.accounting(self.root,
                                datetime(2026, 10, 21, 1, tzinfo=timezone.utc),
                                day="20261020")
        live.assert_not_called()
        archived.assert_called_once()
        self.assertTrue(data["historical_catalog_is_stale"])
        self.assertEqual(data["classification_counts"],
                         {"PROVEN_FIRST_GIT_BEFORE_DEADLINE": 1})
        self.assertEqual(data["scheduled_races_catalog"], 2)
        self.assertEqual(data["not_observed_count"], 1)
        self.assertFalse(data["c1_99_percent_proven"])

    def test_historic_missing_git_proof_does_not_become_success(self):
        self.write("data/site_paper_sim/readiness_history_v215/20261020.json",
                   {"observations": {KEY: {"deadline": "15:53", "reason": "snapshot_missing"}}})
        self.write("data/today.json", {"date": "2026-10-21", "venues": []})
        with patch.object(m, "archived_receipt", return_value={
            "prediction_saved_proven": False, "status": "ARCHIVE_NO_FIRST_GIT_ADD"}):
            data = m.accounting(self.root, datetime(2026, 10, 21, 1, tzinfo=timezone.utc),
                                day="20261020")
        self.assertEqual(data["classification_counts"], {"UNPROVEN_AFTER_DEADLINE": 1})
        self.assertEqual(data["races"][0]["receipt_status"], "ARCHIVE_NO_FIRST_GIT_ADD")

    def test_archived_receipt_fails_closed_without_original_files(self):
        from datetime import timedelta
        due = datetime(2026, 10, 20, 15, 53, tzinfo=m.JST)
        proof = m.archived_receipt(self.root, KEY, due)
        self.assertEqual(proof["status"], "ARCHIVE_NO_SNAPSHOT")
        self.assertFalse(proof["prediction_saved_proven"])

    def test_observation_ended_before_decision_window(self):
        due = datetime(2026, 10, 20, 15, 53, tzinfo=m.JST)
        item = {"last_seen_at": "2026-10-20T06:40:00+00:00",
                "reason": "snapshot_missing", "source_gaps": []}
        report = m.observation_diagnostic(item, due)
        self.assertEqual(report["class"], "NO_OBSERVATION_IN_DECISION_WINDOW")
        self.assertEqual(report["minutes_to_deadline"], 13)

    def test_in_window_source_gap_and_missing_snapshot_separated(self):
        due = datetime(2026, 10, 20, 15, 53, tzinfo=m.JST)
        item = {"last_seen_at": "2026-10-20T06:46:00+00:00",
                "reason": "snapshot_missing", "source_gaps": ["beforeinfo_not_ok"]}
        self.assertEqual(m.observation_diagnostic(item, due)["class"],
                         "SOURCE_GAPS_IN_DECISION_WINDOW")
        item["source_gaps"] = []
        self.assertEqual(m.observation_diagnostic(item, due)["class"],
                         "NO_SNAPSHOT_AT_OBSERVED_DECISION_INSTANT")

    def test_in_window_missing_does_not_become_certified_c1_failure(self):
        self.write("data/site_paper_sim/readiness_history_v215/20261020.json",
                   {"observations": {KEY: {"deadline": "15:53",
                                             "last_seen_at": "2026-10-20T06:46:00+00:00",
                                             "reason": "snapshot_missing", "source_gaps": []}}})
        self.write("data/today.json", {"date": "2026-10-21", "venues": []})
        with patch.object(m, "archived_receipt", return_value={
            "prediction_saved_proven": False, "status": "ARCHIVE_NO_SNAPSHOT"}):
            data = m.accounting(self.root, datetime(2026, 10, 21, 1, tzinfo=timezone.utc),
                                day="20261020")
        self.assertEqual(data["unproven_last_observation_diagnostics"],
                         {"NO_SNAPSHOT_AT_OBSERVED_DECISION_INSTANT": 1})
        self.assertFalse(data["eligible_denominator_verified"])
        self.assertFalse(data["c1_99_percent_proven"])

    def test_historic_source_timings_never_upgrade_eligibility(self):
        due = datetime(2026, 10, 20, 15, 53, tzinfo=m.JST)
        self.write("data/races/" + KEY + ".json", {
            "meta": {"phase": "PRE_RESULT", "results_seen": False,
                     "unlock": False, "scoring": False,
                     "venue_code": "03", "race_no": 11, "deadline": "15:53"},
            "source_audit": {
                "race_card": {"status": "ok", "fetched_at": "2026-10-20T06:47:00+00:00"},
                "beforeinfo": {"status": "ok", "fetched_at": "2026-10-20T06:47:10+00:00"}}})
        self.write("data/site_scratches_v182/" + KEY + ".json", {
            "race_key": KEY, "blocked": False,
            "official_beforeinfo_source_status": "ok",
            "checked_at": "2026-10-20T06:47:20+00:00"})
        self.write("data/site_odds/" + KEY + ".json", {
            "race_key": KEY, "phase": "PRE_RESULT_PURCHASE_ONLY",
            "verified_official_dom_v167": True, "available_count": 120,
            "fetched_at": "2026-10-20T06:47:30+00:00"})
        report = m.historical_source_timing(self.root, KEY, due)
        self.assertTrue(report["all_four_latest_files_in_decision_window"])
        self.assertEqual(report["interpretation"],
                         "LATEST_LOCAL_FILE_TIMINGS_ONLY_NOT_HISTORIC_ELIGIBILITY")
        self.write("data/site_odds/" + KEY + ".json", {
            "race_key": KEY, "phase": "PRE_RESULT_PURCHASE_ONLY",
            "verified_official_dom_v167": True, "available_count": 120,
            "fetched_at": "2026-10-20T06:54:00+00:00"})
        late = m.historical_source_timing(self.root, KEY, due)
        self.assertFalse(late["all_four_latest_files_in_decision_window"])
        self.assertFalse(late["sources"]["official_odds"]["latest_file_in_2_to_10m_window"])

    def test_missing_official_source_timing_cannot_be_counted_ready(self):
        due = datetime(2026, 10, 20, 15, 53, tzinfo=m.JST)
        report = m.historical_source_timing(self.root, KEY, due)
        self.assertFalse(report["all_four_latest_files_in_decision_window"])
        self.assertEqual(sum(x["latest_file_in_2_to_10m_window"]
                             for x in report["sources"].values()), 0)

    def test_unproven_timing_rollup_never_certifies_eligible_miss(self):
        self.write("data/site_paper_sim/readiness_history_v215/20261020.json",
                   {"observations": {KEY: {"deadline": "15:53",
                                             "last_seen_at": "2026-10-20T06:42:00+00:00",
                                             "reason": "snapshot_missing", "source_gaps": []}}})
        self.write("data/today.json", {"date": "2026-10-21", "venues": []})
        with (patch.object(m, "archived_receipt", return_value={
            "prediction_saved_proven": False, "status": "ARCHIVE_NO_SNAPSHOT"}),
              patch.object(m, "historical_source_timing", return_value={
                 "all_four_latest_files_in_decision_window": True,
                 "interpretation": "LATEST_LOCAL_FILE_TIMINGS_ONLY_NOT_HISTORIC_ELIGIBILITY"})):
            report=m.accounting(self.root, datetime(2026, 10, 21, 1, tzinfo=timezone.utc),
                                day="20261020")
        self.assertEqual(report["unproven_latest_source_timing_counts"], {
            "unproven_observed_races": 1,
            "latest_four_sources_in_2_to_10m": 1,
            "latest_four_sources_not_in_2_to_10m": 0,
            "latest_four_sources_prewarm_only": 0})
        self.assertEqual(report["classification_counts"], {"UNPROVEN_AFTER_DEADLINE": 1})
        self.assertFalse(report["eligible_denominator_verified"])
        self.assertFalse(report["c1_99_percent_proven"])

    def test_latest_sources_early_prewarm_does_not_prove_final_git_save(self):
        due = datetime(2026, 10, 20, 15, 53, tzinfo=m.JST)
        self.write("data/races/" + KEY + ".json", {
            "meta": {"phase": "PRE_RESULT", "results_seen": False, "unlock": False,
                     "scoring": False, "venue_code": "03", "race_no": 11,
                     "deadline": "15:53"},
            "source_audit": {
                "race_card": {"status": "ok", "fetched_at": "2026-10-20T06:40:00+00:00"},
                "beforeinfo": {"status": "ok", "fetched_at": "2026-10-20T06:40:10+00:00"}}})
        self.write("data/site_scratches_v182/" + KEY + ".json", {
            "race_key": KEY, "blocked": False,
            "official_beforeinfo_source_status": "ok",
            "checked_at": "2026-10-20T06:40:20+00:00"})
        self.write("data/site_odds/" + KEY + ".json", {
            "race_key": KEY, "phase": "PRE_RESULT_PURCHASE_ONLY",
            "verified_official_dom_v167": True, "available_count": 120,
            "fetched_at": "2026-10-20T06:40:30+00:00"})
        result = m.historical_source_timing(self.root, KEY, due)
        self.assertTrue(result["all_four_latest_files_in_prewarm_window"])
        self.assertTrue(result["latest_files_prewarm_only"])
        self.assertFalse(result["all_four_latest_files_in_decision_window"])

    def test_other_day_or_unverified_catalog_cannot_create_denominator(self):
        self.write("data/today.json", {"date": "2026-10-19", "venues": []})
        with patch.object(m, "receipt") as proof:
            data = m.accounting(self.root, datetime(2026, 10, 20, 6, 54, tzinfo=timezone.utc))
        self.assertEqual(data["classification_counts"], {"UNKNOWN_DEADLINE": 1})
        self.assertIsNone(data["scheduled_races_catalog"])
        proof.assert_not_called()


if __name__ == "__main__":
    unittest.main()
