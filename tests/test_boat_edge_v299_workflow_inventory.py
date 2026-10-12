"""V299 guard against reactivation of old five-minute GitHub writers."""
import unittest
from pathlib import Path
from scripts.boat_edge_v299_workflow_inventory import audit, verify_retired, RETIRED, LIVE

ROOT = Path(__file__).resolve().parents[1]

class WorkflowInventoryTests(unittest.TestCase):
    def test_previous_cron_installers_are_manual_only(self):
        report = audit(ROOT / ".github" / "workflows")
        verify_retired(report)
        items = {x["workflow"]: x for x in report["workflows"]}
        self.assertGreater(report["total_workflows"], 0)
        for name in RETIRED:
            self.assertEqual(items[name]["triggers"], ["workflow_dispatch"])
            self.assertEqual(items[name]["crons"], [])
        self.assertIn("schedule", items[LIVE]["triggers"])
    def test_inventory_is_read_only_and_deterministic(self):
        root = ROOT / ".github" / "workflows"
        self.assertEqual(audit(root), audit(root))
    def test_scheduled_writers_are_reported_not_silently_disabled(self):
        result = audit(ROOT / ".github" / "workflows")
        self.assertIn("BOAT_EDGE_V186_SCRATCH_FRESHNESS.yml", result["scheduled_contents_writers"])
        for retired in RETIRED:
            self.assertNotIn(retired, result["scheduled_contents_writers"])

if __name__ == "__main__":
    unittest.main()
