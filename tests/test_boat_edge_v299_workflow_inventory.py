"""V299 guard against reactivation of old five-minute GitHub writers."""
import unittest
from pathlib import Path
from scripts.boat_edge_v299_workflow_inventory import audit, verify_retired, RETIRED, LIVE

ROOT = Path(__file__).resolve().parents[1]

class WorkflowInventoryTests(unittest.TestCase):
    def test_previous_cron_installers_remain_deleted(self):
        report = audit(ROOT / ".github" / "workflows")
        verify_retired(report)
        items = {x["workflow"]: x for x in report["workflows"]}
        self.assertGreater(report["total_workflows"], 0)
        for name in RETIRED:
            self.assertNotIn(name, items)
        for removed in (
            "auto-update-5min 2.yml", "auto-update-v10 2.yml",
            "auto-update-5min.yml", "auto-update-v10.yml",
            "site-v185-trigger.yml", "BOAT_EDGE_V221_GUARDED_DEDUP.yml",
            "BOAT_EDGE_SITE_RESULTS_V58.zip",
        ):
            self.assertFalse((ROOT / ".github/workflows" / removed).exists(), removed)
        self.assertFalse((ROOT / "scripts/boat_edge_v221_workflow_dedup.py").exists())
        self.assertIn("schedule", items[LIVE]["triggers"])

    def test_v133_history_cannot_compete_with_v229_first_git_freeze(self):
        # Live 2026-10-15 V133 add/add collision on a V229 snapshot. This
        # guard enforces a history-only stage and recomputation after a remote
        # main advance, rather than rebase of a competing first snapshot.
        flow=(ROOT/'.github/workflows/site-v133.yml').read_text(encoding='utf-8')
        stage=flow.split('      - name: Save V133 history',1)[1]
        self.assertIn('git reset --hard origin/main',stage)
        self.assertIn('git clean -fd -- data/site_prediction_snapshots/',stage)
        self.assertIn('git add -A -- data/site_prediction_history/',stage)
        self.assertIn('V133_HISTORY_ONLY_NO_SNAPSHOT_FIRST_GIT_ADD',stage)
        self.assertIn('V133_UNSAFE_FIRST_FREEZE_STAGE_BLOCKED',stage)
        self.assertIn('git push origin HEAD:main',stage)
        self.assertNotIn('git add data/site_prediction_snapshots',stage)
        self.assertNotIn('git pull --rebase',stage)
        self.assertNotIn('git push --force',stage)
        self.assertNotIn('data/formal_predictions/',stage)
        # V229 and V235 keep their independent automated freeze roles.
        inv=audit(ROOT/'.github/workflows')
        by_name={e['workflow']:e for e in inv['workflows']}
        for key in ('BOAT_EDGE_V229_ATOMIC_FREEZE_AUDIT.yml','V235.yml'):
            self.assertIn('schedule',by_name[key]['triggers'])
            self.assertIn('workflow_run',by_name[key]['triggers'])

    def test_v186_scratch_writer_never_rebases_over_newer_withdrawal_evidence(self):
        source=(ROOT/'.github/workflows/BOAT_EDGE_V186_SCRATCH_FRESHNESS.yml').read_text(encoding='utf-8')
        writer=source.split('      - name: Publish only current predeadline unfrozen scratch checks',1)[1]
        self.assertIn('git reset --hard origin/main',writer)
        self.assertIn('git clean -fd -- data/site_scratches_v182/',writer)
        self.assertIn('source_write_allowed(root,key,deadline,now)',writer)
        self.assertIn("0 <= (due-now).total_seconds() <= 26*60",writer)
        self.assertIn('held_explicit.append(key)',writer)
        self.assertIn('V186_UNEXPECTED_STAGED_SOURCE_PATH',writer)
        self.assertIn('V186_SCRATCH_ONLY_FAST_FORWARD_PUBLISHED',writer)
        self.assertNotIn('git rebase',writer)
        self.assertNotIn('git pull --rebase',writer)
        self.assertNotIn('git add -A -- data/site_scratches_v182/',writer)
        self.assertNotIn('git add -- index.html',writer)
        self.assertNotIn('git push --force',writer)
        by_name={entry['workflow']:entry for entry in audit(ROOT/'.github/workflows')['workflows']}
        self.assertIn('schedule',by_name['BOAT_EDGE_V186_SCRATCH_FRESHNESS.yml']['triggers'])

    def test_inventory_is_read_only_and_deterministic(self):
        root = ROOT / ".github" / "workflows"
        self.assertEqual(audit(root), audit(root))
    def test_scheduled_writers_are_reported_not_silently_disabled(self):
        result = audit(ROOT / ".github" / "workflows")
        self.assertIn("BOAT_EDGE_V186_SCRATCH_FRESHNESS.yml", result["scheduled_contents_writers"])
        for retired in RETIRED:
            self.assertNotIn(retired, result["scheduled_contents_writers"])

    def test_v239_retired_without_reintroducing_research_writer(self):
        self.assertFalse((ROOT / ".github/workflows/v239.yml").exists())
        self.assertTrue((ROOT / "scripts/boat_edge_v239_second_tail.py").is_file())
        report = audit(ROOT / ".github/workflows")
        self.assertNotIn("v239.yml", report["scheduled_contents_writers"])
        verify_retired(report)

    def test_v240_retired_without_dropping_research_source(self):
        self.assertFalse((ROOT / ".github/workflows/v240.yml").exists())
        self.assertTrue((ROOT / "scripts/boat_edge_v240_coverage.py").is_file())
        report = audit(ROOT / ".github/workflows")
        self.assertNotIn("v240.yml", report["scheduled_contents_writers"])
        verify_retired(report)

    def test_v183_and_v190_retired_without_loss_of_research_sources(self):
        for name in ("BOAT_EDGE_V183_PROSPECTIVE_SCORE.yml", "BOAT_EDGE_V190.yml"):
            self.assertFalse((ROOT / ".github/workflows" / name).exists(), name)
        for name in ("scripts/site_v183_audit.py", "scripts/site_v184_integrity.py"):
            self.assertTrue((ROOT / name).is_file(), name)
        verify_retired(audit(ROOT / ".github/workflows"))

    def test_primary_collector_and_active_scratch_writer_stay_scheduled(self):
        report = audit(ROOT / ".github" / "workflows")
        entries = {x["workflow"]: x for x in report["workflows"]}
        for name in ("auto-update.yml", "BOAT_EDGE_V186_SCRATCH_FRESHNESS.yml", "V235.yml"):
            with self.subTest(name=name):
                self.assertIn("schedule", entries[name]["triggers"])
                self.assertIn("workflow_dispatch", entries[name]["triggers"])
        self.assertNotIn("BOAT_EDGE_V185_THIRD_ROLE_FRESH_CHALLENGER.yml", entries)
        self.assertNotIn("BOAT_EDGE_V221_GUARDED_DEDUP.yml", entries)
        self.assertNotIn("site-v185-trigger.yml", entries)

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
        targets = (("v236.yml", 3, "3,18,33,48", "boat_edge_v236_hit_rate.py"),)
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
                    self.assertIn("V236_ACCELERATE_ONLY_VERIFIED_PROSPECTIVE_CANDIDATE",src)
                    self.assertIn("success=true",src)
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

    def test_v199_retired_and_current_first_git_owners_remain(self):
        self.assertFalse((ROOT / ".github/workflows/BOAT_EDGE_V199_PROSPECTIVE_SCENARIO_ABLATIONS.yml").exists())
        self.assertTrue((ROOT / "scripts/site_v199_research.py").is_file())
        for name in ("V234.yml", "V235.yml"):
            source=(ROOT / ".github/workflows" / name).read_text(encoding="utf-8")
            self.assertIn("scripts/boat_edge_v230_fast_lane.py", source)
            self.assertIn("  schedule:", source)

    def test_retired_v249_and_v134_cannot_reintroduce_legacy_writers(self):
        root = ROOT / ".github/workflows"
        for name in ("v249.yml", "site-v134.yml"):
            self.assertFalse((root / name).exists(), name)
        history=(root / "site-v133.yml").read_text(encoding="utf-8")
        self.assertIn('cron: "4-59/5 * * * *"', history)
        self.assertIn("if: ${{ false }}", history)
        primary=(root / "V235.yml").read_text(encoding="utf-8")
        atomic=(root / "BOAT_EDGE_V229_ATOMIC_FREEZE_AUDIT.yml").read_text(encoding="utf-8")
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
