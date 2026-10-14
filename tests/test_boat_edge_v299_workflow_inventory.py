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


    def test_01_site_only_post_result_scores_no_longer_push_each_5_minutes(self):
        """Cut Pages build churn without slowing prospective unseen freezes."""
        targets = (
            ("v236.yml", 3, "3,18,33,48", "boat_edge_v236_hit_rate.py"),
            ("v239.yml", 4, "9,24,39,54", "boat_edge_v239_second_tail.py"),
            ("v240.yml", 1, "11,26,41,56", "boat_edge_v240_coverage.py"),
            ("v254-third-tail-shadow.yml", 3, "13,28,43,58",
             "boat_edge_v254_third_tail.py"),
        )
        for filename, offset, score_slot, script in targets:
            with self.subTest(workflow=filename):
                src = (ROOT / ".github/workflows" / filename).read_text(encoding="utf-8")
                import re
                crons = re.findall(r"^\s+- cron: '([^']+)'$", src, re.MULTILINE)
                self.assertEqual(len(crons), 3)
                minutes = []
                for cron in crons:
                    fields = cron.split()
                    self.assertEqual(fields[1:], ["0-14,23", "*", "*", "*"])
                    minutes.extend(int(t) for t in fields[0].split(","))
                self.assertEqual(sorted(minutes), list(range(offset, 60, 5)))
                self.assertEqual(len(minutes), len(set(minutes)))
                self.assertIn(f"scripts/{script} freeze", src)
                self.assertIn(f"scripts/{script} score", src)
                self.assertLess(src.index(f"scripts/{script} freeze"),
                                src.index(f"scripts/{script} score"))
                guard = ("github.event_name == 'schedule' && "
                         f"github.event.schedule == '{score_slot} 0-14,23 * * *'")
                if filename == "v236.yml":
                    # Ordinary SITE results remain staggered. A fast existing
                    # five-minute tick can run the same score command ONLY
                    # for an independently first-Git-frozen V2/V3 research
                    # candidate with an already confirmed SITE official result.
                    # This must not add any scheduled workflows or permit the
                    # whole retrospective cohort to push every five minutes.
                    self.assertIn("V236_SCHEDULED_TICK", src)
                    self.assertIn("pending_confirmed_prospective_score", src)
                    self.assertIn("V236_NO_CONFIRMED_PROSPECTIVE_SCORE", src)
                    self.assertIn("V236_PENDING_CONFIRMED_PROSPECTIVE_SCORE", src)
                    self.assertIn("github.event_name == 'schedule'", src)
                    self.assertIn(
                        'if [[ "$GITHUB_EVENT_NAME" == \'schedule\' && '
                        '"$V236_SCHEDULED_TICK" != '
                        "'3,18,33,48 0-14,23 * * *' ]]",
                        src)
                    self.assertIn('success=true\\n                break', src)
                    # The fixed prior 15-minute schedule is still present.
                    self.assertIn(f"'{score_slot} 0-14,23 * * *'", src)
                else:
                    self.assertEqual(src.count(guard), 1)
                self.assertIn("github.event_name == 'workflow_dispatch'", src)
                self.assertIn("github.event_name == 'push'", src)
                # Freeze still runs on all twelve distinct five-minute
                # schedule ticks. Replaying the same freeze on each V235
                # completion causes duplicate main pushes / cancelled Pages.
                from scripts.boat_edge_v299_workflow_inventory import event_block
                events = event_block(src)
                if filename in ("v236.yml", "v239.yml", "v240.yml"):
                    self.assertNotRegex(events, r"(?m)^  workflow_run:")
                    self.assertNotIn("github.event.workflow_run", src)
                else:
                    # V254 has separate V286 event-driven provenance
                    # dependencies; it is not part of this dedup change.
                    self.assertRegex(events, r"(?m)^  workflow_run:")
                self.assertIsNotNone(re.search(r"(?m)^  schedule:", events))
                self.assertIn("workflow_dispatch:", events)

    def test_v234_original_5m_future_freezes_and_staggered_result_scoring(self):
        """Protect 12 prospective freezes; delay only retrospective SITE scoring."""
        import re
        workflow = (ROOT / ".github/workflows/V234.yml").read_text(encoding="utf-8")
        slots = re.findall(r"^\s+- cron: '([^']+)'$", workflow, re.MULTILINE)
        self.assertEqual(len(slots), 3)
        minutes = []
        for slot in slots:
            minute, hour, day, month, weekday = slot.split()
            self.assertEqual((hour, day, month, weekday),
                             ("0-14,23", "*", "*", "*"))
            minutes.extend(map(int, minute.split(",")))
        self.assertEqual(sorted(minutes), list(range(4, 60, 5)))
        self.assertEqual(len(minutes), len(set(minutes)))
        self.assertIn("github.event.schedule == '4,19,34,49 0-14,23 * * *'",
                      workflow)
        freeze = workflow.index("      - name: Immutable pre-result source prediction cohort")
        future = workflow.index("      - name: V275 immediately freeze qualifying V254")
        scored = workflow.index("      - name: Only after pre-result commit - score already confirmed SITE results")
        self.assertLess(freeze, future)
        self.assertLess(future, scored)
        self.assertNotIn("data/site_results/", workflow[freeze:future])
        self.assertNotIn("data/site_results/", workflow[future:scored])
        score = workflow[scored:]
        self.assertIn("python3 scripts/boat_edge_v234_settle.py", score)
        self.assertIn("git commit -m 'V234 score confirmed post-result", score)

    def test_v199_all_future_freeze_minutes_preserved_with_scoring_only_each_15m(self):
        """Do not lose first-addition research provenance to save Pages builds."""
        import re
        workflow = (ROOT / ".github/workflows/BOAT_EDGE_V199_PROSPECTIVE_SCENARIO_ABLATIONS.yml").read_text(encoding="utf-8")
        slots = re.findall(r"^\s+- cron: '([^']+)'$", workflow, re.MULTILINE)
        self.assertEqual(len(slots), 3)
        minutes = []
        for slot in slots:
            minute, hour, day, month, weekday = slot.split()
            self.assertEqual((hour, day, month, weekday),
                             ("0-14,23", "*", "*", "*"))
            minutes.extend(map(int, minute.split(",")))
        self.assertEqual(sorted(minutes), list(range(0, 60, 5)))
        self.assertEqual(len(set(minutes)), 12)
        freeze = workflow.index("      - name: Freeze only eligible future races without reading results")
        replay = workflow.index("      - name: Independently replay first Git addition before optional site-only result scoring")
        report = workflow.index("      - name: Save only research evidence with safe concurrent-write retry")
        self.assertLess(freeze, replay)
        self.assertLess(replay, report)
        gate = ("github.event_name == 'schedule' && "
                "github.event.schedule == '0,15,30,45 0-14,23 * * *'")
        self.assertEqual(workflow.count(gate), 2)
        self.assertIn("python3 scripts/site_v199_research.py freeze", workflow[freeze:replay])
        self.assertNotIn("python3 scripts/site_v199_research.py score", workflow[freeze:replay])
        self.assertIn("python3 scripts/site_v199_research.py score", workflow[replay:report])
        self.assertIn("python3 scripts/site_v199_research.py score", workflow[report:])
        self.assertIn("github.event_name == 'workflow_dispatch'", workflow)
        self.assertIn("github.event_name == 'push'", workflow)

    def test_01_retire_obsolete_v249_and_decouple_todo_from_five_minute_history(self):
        """Protect live Pages from obsolete UI installs and redundant TODO pushes."""
        root = ROOT / ".github/workflows"
        old_ui = (root / "v249.yml").read_text(encoding="utf-8")
        todo = (root / "site-v134.yml").read_text(encoding="utf-8")
        history = (root / "site-v133.yml").read_text(encoding="utf-8")
        # V249 is no longer byte-identical to today's newer mobile CSS.
        # Existing safety checks remain for explicit manual legacy inspection.
        self.assertIn("  workflow_dispatch:", old_ui)
        self.assertNotIn("  schedule:", old_ui)
        self.assertNotIn("  push:", old_ui)
        self.assertIn("V249_VERIFIED_UI_RESOURCE_DRIFT_", old_ui)
        self.assertIn("assets/boat_edge_v249_focus.css", old_ui)
        # The user-facing V133 FINAL15M history keeps its 5-minute cadence,
        # while the TODO documentation no longer republishes on every run.
        self.assertIn('cron: "*/5 * * * *"', history)
        self.assertIn("  workflow_dispatch:", todo)
        self.assertIn("  schedule:", todo)
        self.assertIn("cron: '38 * * * *'", todo)
        self.assertNotIn("  workflow_run:", todo)
        self.assertIn("git add -- BOAT_EDGE_CURRENT_TODO.md", todo)
        # V134's fix cannot disable or backdate the prediction source freeze.
        primary = (root / "V235.yml").read_text(encoding="utf-8")
        atomic = (root / "BOAT_EDGE_V229_ATOMIC_FREEZE_AUDIT.yml").read_text(encoding="utf-8")
        self.assertIn("  schedule:", primary)
        self.assertIn("  schedule:", atomic)

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
        # V216 preserves the original five-minute PRE_RESULT freeze and
        # paper selection slots while staggering only retrospective settlement.
        import re
        slots = re.findall(r"^\s+- cron: '([^']+)'$", workflow, re.MULTILINE)
        self.assertEqual(len(slots), 3)
        minutes = []
        for cron in slots:
            fields = cron.split()
            self.assertEqual(fields[1:], ["*", "*", "*", "*"])
            minutes.extend(int(m) for m in fields[0].split(","))
        self.assertEqual(sorted(minutes), list(range(4, 60, 5)))
        self.assertEqual(len(set(minutes)), 12)
        self.assertIn("if: ${{ github.event_name != 'schedule' || github.event.schedule == '14,29,44,59 * * * *' }}", later)
        self.assertLess(later.index("github.event.schedule"),
                        later.index("scripts/boat_edge_v214_shadow.py settle"))


if __name__ == "__main__":
    unittest.main()
