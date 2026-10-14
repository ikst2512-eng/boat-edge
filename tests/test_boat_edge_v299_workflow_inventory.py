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

    def test_v356_retired_v185_relay_has_no_dispatch_or_write_permission(self):
        relay = ROOT / ".github/workflows/site-v185-trigger.yml"
        src = relay.read_text(encoding="utf-8")
        self.assertNotIn("workflow_run:", src)
        self.assertNotIn("actions: write", src)
        self.assertNotIn("curl ", src)
        self.assertNotIn("/dispatches", src)
        report = audit(ROOT / ".github" / "workflows")
        row = next(x for x in report["workflows"] if x["workflow"] == relay.name)
        self.assertEqual(row["triggers"], ["workflow_dispatch"])
        self.assertFalse(row["scheduled_write_candidate"])

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


    def test_v216_one_git_receipt_for_pre_result_readiness_and_shadow(self):
        """Avoid two Pages-invalidating commits while keeping settled phases separate."""
        workflow = (ROOT / ".github/workflows/BOAT_EDGE_V216_SOURCE_DIAGNOSTIC.yml").read_text(encoding="utf-8")
        first = "      - name: Freeze PRE_RESULT diagnostics and shadow evidence in one Git commit"
        next_step = "      - name: Continue approved-only daily 50000 yen paper selection BEFORE results"
        self.assertIn(first, workflow)
        self.assertIn(next_step, workflow)
        early = workflow.split(first, 1)[1].split(next_step, 1)[0]
        self.assertIn("python3 scripts/boat_edge_v215_readiness.py", early)
        self.assertIn("python3 scripts/boat_edge_v214_shadow.py freeze", early)
        self.assertLess(early.index("scripts/boat_edge_v215_readiness.py"),
                        early.index("scripts/boat_edge_v214_shadow.py freeze"))
        self.assertLess(early.index("scripts/boat_edge_v214_shadow.py freeze"),
                        early.index("git commit -m"))
        self.assertEqual(early.count("git commit -m"), 1)
        self.assertEqual(early.count("git push origin HEAD:main"), 1)
        self.assertIn("V216_FORMAL_RESULT_UNSEEN_GUARD_BLOCKED", early)
        self.assertNotIn("scripts/boat_edge_v214_shadow.py settle", early)
        self.assertNotIn("scripts/boat_edge_v211_paper_sim.py settle", early)
        self.assertNotIn("data/site_results/", early)
        late = workflow.split(next_step, 1)[1]
        self.assertIn("scripts/boat_edge_v211_paper_sim.py select", late)
        self.assertIn("scripts/boat_edge_v214_shadow.py settle", late)
        self.assertIn("scripts/boat_edge_v211_paper_sim.py settle", late)
        self.assertEqual(workflow.count("git commit -m"), 3)
        later = workflow.split("      - name: Settle earlier frozen shadow and paper ledgers in one Git commit",1)[1]
        self.assertIn("python3 scripts/boat_edge_v214_shadow.py settle",later)
        self.assertIn("python3 scripts/boat_edge_v211_paper_sim.py settle",later)
        self.assertEqual(later.count("git commit -m"),1)
        self.assertEqual(later.count("git push origin HEAD:main"),1)
        self.assertIn("V216_SETTLE_FORMAL_FRESH_GUARD_BLOCKED",later)
        self.assertIn("V216_SETTLEMENT_FORBIDDEN_STAGED_FILES_",later)
        self.assertIn("cron: '4,9,14,19,24,29,34,39,44,49,54,59 * * * *'", workflow)


if __name__ == "__main__":
    unittest.main()
