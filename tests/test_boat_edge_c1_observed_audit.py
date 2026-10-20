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

    def test_other_day_or_unverified_catalog_cannot_create_denominator(self):
        self.write("data/today.json", {"date": "2026-10-19", "venues": []})
        with patch.object(m, "receipt") as proof:
            data = m.accounting(self.root, datetime(2026, 10, 20, 6, 54, tzinfo=timezone.utc))
        self.assertEqual(data["classification_counts"], {"UNKNOWN_DEADLINE": 1})
        self.assertIsNone(data["scheduled_races_catalog"])
        proof.assert_not_called()


if __name__ == "__main__":
    unittest.main()
