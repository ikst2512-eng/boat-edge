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

    def test_v221_cleanup_is_manual_only(self):
        report = audit(ROOT / ".github" / "workflows")
        entries = {x["workflow"]: x for x in report["workflows"]}
        name = "BOAT_EDGE_V221_GUARDED_DEDUP.yml"
        self.assertEqual(entries[name]["triggers"], ["workflow_dispatch"])
        self.assertEqual(entries[name]["crons"], [])
        self.assertNotIn(name, report["scheduled_contents_writers"])

    def test_legacy_relay_has_no_auto_dispatch_or_action_write_permission(self):
        path = ROOT / ".github" / "workflows" / "site-v185-trigger.yml"
        source = path.read_text(encoding="utf-8")
        items = {x["workflow"]: x for x in audit(ROOT / ".github" / "workflows")["workflows"]}
        entry = items[path.name]
        self.assertEqual(entry["triggers"], ["workflow_dispatch"])
        self.assertFalse(entry["contents_write"])
        self.assertNotIn("workflow_run:", source)
        self.assertNotIn("actions: write", source)
        self.assertNotIn("dispatches", source)
        self.assertNotIn("api.github.com", source)

    def test_plain_and_quoted_on_keys_are_equivalent(self):
        from tempfile import TemporaryDirectory
        styles = ("on", "'on'", '"on"')
        with TemporaryDirectory() as folder:
            root = Path(folder)
            for index, style in enumerate(styles):
                (root / f"fixture{index}.yml").write_text(
                    "name: fixture\n" + style + ": # trigger key\n"
                    "  workflow_dispatch:\n"
                    "  schedule:\n"
                    "    - cron: '29 20 * * *'\n"
                    "permissions:\n"
                    "  contents: write\n"
                    "jobs:\n"
                    "  stub:\n"
                    "    runs-on: ubuntu-latest\n",
                    encoding="utf-8",
                )
            (root / "unrelated.yml").write_text(
                "name: unrelated\n"
                "'on':\n"
                "  workflow_dispatch:\n"
                "env:\n"
                "  schedule: should-not-be-counted\n"
                "permissions:\n"
                "  contents: write\n",
                encoding="utf-8",
            )
            report = audit(root)
            self.assertEqual(report["scheduled"], len(styles))
            self.assertEqual(len(report["scheduled_contents_writers"]), len(styles))
            for entry in report["workflows"]:
                if entry["workflow"] == "unrelated.yml":
                    self.assertEqual(entry["triggers"], ["workflow_dispatch"])
                    continue
                self.assertEqual(entry["triggers"], ["workflow_dispatch", "schedule"])
                self.assertEqual(entry["crons"], ["29 20 * * *"])

if __name__ == "__main__":
    unittest.main()
