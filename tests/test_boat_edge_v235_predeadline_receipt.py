#!/usr/bin/env python3
"""No-network prospective receipt tests; never read results/formal files."""
import hashlib
import json
import os
from datetime import datetime
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from scripts.boat_edge_v235_predeadline_receipt import JST, receipt, choose

KEY = "20261014-14-01"


def save(root, path, obj):
    target = root / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(obj, ensure_ascii=False) + "\n", encoding="utf-8")
    return target


def source(root):
    save(root, "data/today.json", {
        "date": "2026-10-14", "venues": [{"venue": "鳴門", "races": [
            {"race_key": KEY, "deadline": "08:35"}]}]})
    save(root, f"data/races/{KEY}.json", {
        "race_key": KEY, "meta": {"phase": "PRE_RESULT",
                                   "results_seen": False, "unlock": False, "scoring": False},
        "source_audit": {"race_card": {"status": "ok"},
                         "beforeinfo": {"status": "not_in_window"}}})


def frozen(root):
    snap = {
        "race_key": KEY, "schema_version": "boat-edge-server-site-final-v123",
        "snapshot_window": "FINAL_15M", "prediction_kind": "SITE_REFERENCE_V122",
        "selection_policy": "V122_SCENARIO_AWARE_PROBABILITY_FIRST",
        "first_saved_at": "2026-10-14T08:28:00+09:00",
        "saved_at": "2026-10-14T08:28:00+09:00",
        "guards": {"results_seen": False, "unlock": False, "scoring": False},
        "modes": {"hit": {"tickets": [{"combo": x} for x in (
            "1-2-3", "1-2-4", "1-2-5", "1-2-6", "1-3-2", "1-3-4",
            "1-3-5", "1-3-6", "1-4-2", "1-4-3")]}}}
    path = save(root, f"data/site_prediction_snapshots/{KEY}.json", snap)
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    save(root, f"data/site_prediction_audit/{KEY}.json", {
        "race_key": KEY, "pass": True, "latest_snapshot_sha256": digest})
    return path


class V235Proof(unittest.TestCase):
    def test_free_official_odds_completion_wakes_existing_v235_directly(self):
        # Free public-repo standard Actions only: reuse the existing V71 run.
        # No new cron, Render, prediction writer, or weakened freeze window.
        root = Path(__file__).resolve().parents[1]
        v235 = (root / '.github/workflows/V235.yml').read_text(encoding='utf-8')
        preamble = v235.split('\npermissions:', 1)[0]
        self.assertIn("      - 'BOAT EDGE 自動更新'", preamble)
        self.assertIn("      - 'BOAT EDGE 3連単オッズ更新 V71'", preamble)
        self.assertIn('    types: [completed]', preamble)
        self.assertEqual(preamble.count('    - cron:'), 2)
        self.assertIn("github.event.workflow_run.conclusion == 'success'", v235)
        self.assertIn("github.event.workflow_run.head_branch == 'main'", v235)
        self.assertIn('github.event.workflow_run.head_repository.full_name == github.repository', v235)
        self.assertIn('group: boat-edge-v235-conflict-safe-source-and-scoring', v235)
        self.assertIn('cancel-in-progress: false', v235)
        self.assertIn('V235_INITIAL_SNAPSHOT_PUBLISHED', v235)
        # Downstream V229 must not be listened to by V235 (no cycle).
        self.assertNotIn('BOAT EDGE V229 - Atomic Site Freeze and Pre-result Audit', preamble)
        odds = (root / '.github/workflows/site-odds.yml').read_text(encoding='utf-8')
        odds_events = odds.split('\npermissions:', 1)[0]
        self.assertNotIn('BOAT EDGE V235 - Stable Autonomous Prediction Freeze and Verified Scoring', odds_events)

    def test_v216_independent_schedule_source_ready_wakes_existing_v235_only(self):
        # Production Toda 1R 2026-10-16: source-ready first Git at 10:41:39,
        # 10:47 deadline, V235 prior wake at 10:40 was skipped. Reuse V216
        # schedule completion; reject nested workflow_run to avoid feedback.
        root = Path(__file__).resolve().parents[1]
        flow = (root/'.github/workflows/V235.yml').read_text(encoding='utf-8')
        preamble = flow.split('\npermissions:', 1)[0]
        job = flow.split('  freeze-then-score-site-only:\n', 1)[1].split('    runs-on:', 1)[0]
        self.assertEqual(preamble.count('  workflow_run:'), 1)
        self.assertEqual(preamble.count('  schedule:'), 1)
        self.assertEqual(preamble.count('    - cron:'), 2)
        self.assertIn("      - 'BOAT EDGE V216 - Identify Exact Pre-Deadline Source Gaps'", preamble)
        self.assertIn("github.event.workflow_run.name == 'BOAT EDGE V216 - Identify Exact Pre-Deadline Source Gaps'", job)
        self.assertIn("github.event.workflow_run.event == 'schedule'", job)
        self.assertIn("github.event.workflow_run.conclusion == 'success'", job)
        self.assertIn("github.event.workflow_run.head_branch == 'main'", job)
        self.assertIn("github.event.workflow_run.head_repository.full_name == github.repository", job)
        # Preserve primary V71/collector signals and no feedback to V216.
        self.assertIn("github.event.workflow_run.name == 'BOAT EDGE 自動更新'", job)
        self.assertIn("github.event.workflow_run.name == 'BOAT EDGE 3連単オッズ更新 V71'", job)
        source = (root/'.github/workflows/BOAT_EDGE_V216_SOURCE_DIAGNOSTIC.yml').read_text(encoding='utf-8')
        upstream = source.split('\npermissions:', 1)[0]
        self.assertNotIn('BOAT EDGE V235 - Stable Autonomous Prediction Freeze and Verified Scoring', upstream)
        self.assertIn("cron: '4,19,34,49 * * * *'", upstream)
        self.assertIn("cron: '9,24,39,54 * * * *'", upstream)
        self.assertIn("cron: '14,29,44,59 * * * *'", upstream)
        self.assertIn('group: boat-edge-v235-conflict-safe-source-and-scoring', flow)
        self.assertIn('cancel-in-progress: false', flow)
        self.assertIn('V235_INITIAL_SNAPSHOT_PUBLISHED', flow)
        self.assertNotIn('BOAT EDGE V229 - Atomic Site Freeze and Pre-result Audit', preamble)

    def test_first_three_morning_races_keep_multiple_free_scheduled_wakes(self):
        # ①-1C: This checks planned wake coverage, NOT actual dispatch,
        # source readiness, Git-first-save or the independent 99% denominator.
        # No new paid Cron, replay, result access or prediction writer.
        import re
        from datetime import timedelta, timezone
        root = Path(__file__).resolve().parents[1]
        files = {
            'v235': 'V235.yml',
            'v229': 'BOAT_EDGE_V229_ATOMIC_FREEZE_AUDIT.yml',
            'v216': 'BOAT_EDGE_V216_SOURCE_DIAGNOSTIC.yml',
            'collector': 'auto-update.yml',
            'official_odds': 'site-odds.yml',
        }
        expected_cron_counts = {
            'v235': 2, 'v229': 2, 'v216': 3,
            'collector': 1, 'official_odds': 1,
        }

        def field_set(expr, max_value):
            fields = set()
            for part in expr.split(','):
                if part == '*':
                    fields.update(range(max_value + 1))
                elif part.startswith('*/'):
                    fields.update(range(0, max_value + 1, int(part[2:])))
                elif '-' in part:
                    left, right = map(int, part.split('-', 1))
                    fields.update(range(left, right + 1))
                else:
                    fields.add(int(part))
            return fields

        schedules = {}
        for name, file in files.items():
            workflow = (root / '.github/workflows' / file).read_text(encoding='utf-8')
            header = workflow.split('\\npermissions:', 1)[0]
            crons = re.findall(r'^\\s+- cron: [\\\'\\"](.*?)[\\\'\\"]\\s*        # Gate1C: Future V230 code changes MUST carry a reviewed V235 pin
        # update or fail PR CI before live pre-result collection/freeze.
        root=Path(__file__).resolve().parents[1]
        filename='scripts/boat_edge_v230_fast_lane.py'
        raw=(root/filename).read_bytes()
        git_blob=hashlib.sha1(b'blob '+str(len(raw)).encode('ascii')+b'\x00'+raw).hexdigest()
        workflow=(root/'.github/workflows/V235.yml').read_text(encoding='utf-8')
        self.assertIn(f"'{filename}:{git_blob}'",workflow)
        self.assertIn('test "$(git hash-object "$path")" = "$sha"',workflow)

    def test_window_does_not_invent_a_prediction(self):
        with tempfile.TemporaryDirectory() as base:
            root = Path(base)
            source(root)
            early = receipt(root, datetime(2026, 10, 14, 8, 10, tzinfo=JST))
            self.assertEqual(early["status"], "BEFORE_SOURCE_WINDOW")
            self.assertFalse(early["prediction_saved_proven"])
            self.assertEqual(early["race_key"], KEY)
            active = receipt(root, datetime(2026, 10, 14, 8, 28, tzinfo=JST))
            self.assertEqual(active["status"], "SOURCE_WINDOW_NO_SNAPSHOT")
            self.assertFalse(active["prediction_saved_proven"])

    def test_1r_priority_advances_to_next_race_after_deadline(self):
        with tempfile.TemporaryDirectory() as base:
            root = Path(base)
            source(root)
            catalog = json.loads((root / "data/today.json").read_text())
            catalog["venues"][0]["races"].append({
                "race_key": "20261014-14-02", "deadline": "09:01"})
            save(root, "data/today.json", catalog)
            before = datetime(2026, 10, 14, 8, 20, tzinfo=JST)
            after = datetime(2026, 10, 14, 8, 38, tzinfo=JST)
            self.assertEqual(choose(root, before)[1], KEY)
            self.assertEqual(choose(root, after)[1], "20261014-14-02")
            self.assertEqual(choose(root, after, requested=KEY)[1], KEY)

    def test_live_v230_target_wins_over_expired_two_minute_grace(self):
        # 2026-10-16 production regression: 10:30:32 receipt picked expired
        # Heiwajima 1R while V230 successfully froze Ashiya 5R (10:34).
        with tempfile.TemporaryDirectory() as base:
            root = Path(base)
            expired = "20261016-04-01"
            live = "20261016-21-05"
            save(root, "data/today.json", {
                "date": "2026-10-16", "venues": [
                    {"venue": "平和島", "races": [{"race_key": expired, "deadline": "10:30"}]},
                    {"venue": "芦屋", "races": [{"race_key": live, "deadline": "10:34"}]}
                ]})
            save(root, "data/site_autopilot/v230_fast_current.json", {
                "day_jst": "20261016", "targets": [live],
                "outcomes": {live: "fresh_verified"}})
            now = datetime(2026, 10, 16, 10, 30, 32, tzinfo=JST)
            self.assertEqual(choose(root, now)[1], live)
            self.assertEqual(receipt(root, now)["race_key"], live)
            self.assertEqual(choose(root, now, requested=expired)[1], expired)

    def test_no_v230_status_still_prefers_future_over_expired_grace(self):
        with tempfile.TemporaryDirectory() as base:
            root = Path(base)
            save(root, "data/today.json", {
                "date": "2026-10-16", "venues": [
                    {"venue": "平和島", "races": [
                        {"race_key": "20261016-04-01", "deadline": "10:30"},
                        {"race_key": "20261016-04-02", "deadline": "10:53"}]}
                ]})
            now = datetime(2026, 10, 16, 10, 30, 32, tzinfo=JST)
            self.assertEqual(choose(root, now)[1], "20261016-04-02")

    def test_local_only_not_a_git_commit(self):
        with tempfile.TemporaryDirectory() as base:
            root = Path(base)
            source(root)
            frozen(root)
            candidate = receipt(root, datetime(2026, 10, 14, 8, 29, tzinfo=JST))
            self.assertEqual(candidate["status"], "LOCAL_SNAPSHOT_NOT_FIRST_GIT_COMMITTED")
            self.assertFalse(candidate["prediction_saved_proven"])
            self.assertEqual(candidate["model_id"], "not_stored")
            self.assertEqual(candidate["prediction_kind"], "SITE_REFERENCE_V122")
            self.assertEqual(len(candidate["top10"]), 10)

    def test_exact_sha_first_added_commit_before_deadline(self):
        with tempfile.TemporaryDirectory() as base:
            root = Path(base)
            source(root)
            path = frozen(root)
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            subprocess.run(["git", "config", "user.name", "Test"], cwd=root, check=True)
            subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=root, check=True)
            subprocess.run(["git", "add", "data/today.json", "data/races",
                            "data/site_prediction_snapshots", "data/site_prediction_audit"],
                           cwd=root, check=True)
            env = os.environ.copy()
            env["GIT_AUTHOR_DATE"] = "2026-10-14T08:29:00+09:00"
            env["GIT_COMMITTER_DATE"] = "2026-10-14T08:29:00+09:00"
            subprocess.run(["git", "commit", "-qm", "prospective proof"], cwd=root,
                           env=env, check=True)
            result = receipt(root, datetime(2026, 10, 14, 8, 31, tzinfo=JST))
            self.assertEqual(result["status"], "SITE_FIRST_GIT_COMMIT_BEFORE_DEADLINE")
            self.assertTrue(result["prediction_saved_proven"])
            self.assertEqual(result["snapshot_sha256"], hashlib.sha256(path.read_bytes()).hexdigest())
            self.assertEqual(result["first_git_snapshot_sha256"], result["snapshot_sha256"])
            self.assertEqual(len(result["first_git_commit"]), 40)
            self.assertTrue(result["first_git_commit_at"].startswith("2026-10-14T08:29:00"))

    def test_git_first_commit_after_deadline_is_not_a_valid_save(self):
        with tempfile.TemporaryDirectory() as base:
            root = Path(base)
            source(root)
            frozen(root)
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            subprocess.run(["git", "config", "user.name", "Test"], cwd=root, check=True)
            subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=root, check=True)
            subprocess.run(["git", "add", "data/today.json", "data/races",
                            "data/site_prediction_snapshots", "data/site_prediction_audit"],
                           cwd=root, check=True)
            env = os.environ.copy()
            env["GIT_AUTHOR_DATE"] = "2026-10-14T08:36:00+09:00"
            env["GIT_COMMITTER_DATE"] = "2026-10-14T08:36:00+09:00"
            subprocess.run(["git", "commit", "-qm", "late publish not prospective"],
                           cwd=root, env=env, check=True)
            result = receipt(root, datetime(2026, 10, 14, 8, 37, tzinfo=JST))
            self.assertEqual(result["status"], "FIRST_GIT_COMMIT_NOT_SOURCE_BOUND_PREDEADLINE")
            self.assertFalse(result["prediction_saved_proven"])

    def test_audit_failure_fails_closed(self):
        with tempfile.TemporaryDirectory() as base:
            root = Path(base)
            source(root)
            frozen(root)
            save(root, f"data/site_prediction_audit/{KEY}.json", {
                "pass": True, "latest_snapshot_sha256": "0" * 64})
            result = receipt(root, datetime(2026, 10, 14, 8, 31, tzinfo=JST))
            self.assertEqual(result["status"], "SNAPSHOT_OR_V229_AUDIT_UNVERIFIED")
            self.assertFalse(result["prediction_saved_proven"])

    def test_v230_script_mode_requires_repo_root_pythonpath(self):
        # -m unittest from cwd implicitly sees the repo root, but executing
        # scripts/boat_edge_v230_fast_lane.py directly does not. Keep the
        # original safety-lock import resolvable in both V235 and V230 owners.
        root = Path(__file__).resolve().parents[1]
        commands = {
            ".github/workflows/V235.yml":
                "PYTHONPATH=.:scripts PYTHONDONTWRITEBYTECODE=1 python3 "
                "scripts/boat_edge_v230_fast_lane.py --workers 8 --retry-imminent",
            ".github/workflows/BOAT_EDGE_V230_FAST_OFFICIAL_PREDEADLINE.yml":
                "PYTHONPATH=.:scripts PYTHONDONTWRITEBYTECODE=1 python3 "
                "scripts/boat_edge_v230_fast_lane.py",
        }
        for path, command in commands.items():
            text = (root / path).read_text(encoding="utf-8")
            self.assertIn(command, text)
        env = dict(os.environ)
        env["PYTHONPATH"] = ".:scripts"
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        result = subprocess.run(
            [sys.executable, "scripts/boat_edge_v230_fast_lane.py", "--help"],
            cwd=root, env=env, capture_output=True, text=True, timeout=15,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("--retry-imminent", result.stdout)

    def test_workflow_has_0820_jst_owner_without_duplicate_writers(self):
        text = (Path(__file__).resolve().parents[1] /
                ".github/workflows/V235.yml").read_text(encoding="utf-8")
        self.assertIn("cron: '20 23 * * *'", text)
        self.assertIn("python3 scripts/boat_edge_v230_fast_lane.py --workers 8 --retry-imminent", text)
        self.assertNotIn("--priority-race-key 20261014-14-01", text)
        self.assertIn("python3 scripts/boat_edge_v232_pre_result_cohort.py", text)
        self.assertIn("python3 scripts/boat_edge_v235_predeadline_receipt.py", text)
        self.assertIn("V235_END_TO_END_SITE_PRE_RESULT_COHORT_VERIFIED", text)
        # A local predeadline snapshot is not proof of a timely first Git commit.
        self.assertIn("V235_TAKEOVER_CANDIDATE=1", text)
        self.assertIn("V235_TAKEOVER_FIRST_GIT_PROOF", text)
        self.assertIn("V235_FIRST_GIT_PROOF_REQUIRED_KEEP_V233", text)
        self.assertIn("if: ${{ !cancelled() }}", text)
        self.assertIn("env.write('V235_TAKEOVER_VERIFIED=1' + chr(10))", text)
        self.assertLess(text.index("V235_TAKEOVER_CANDIDATE=1"),
                        text.index("V235_TAKEOVER_FIRST_GIT_PROOF"))
        self.assertLess(text.index("V235_TAKEOVER_FIRST_GIT_PROOF"),
                        text.index("V235_TAKEOVER_VERIFIED=1' + chr(10)"))
        self.assertLess(text.index("V235_TAKEOVER_VERIFIED=1' + chr(10)"),
                        text.index("Disable obsolete V234 and V233"))
        self.assertIn("V235_KEEP_V233_UNTIL_NEW_PRE_RESULT_EVIDENCE_IS_COMMITTED", text)
        for unsafe in ("results_seen=true", "scoring=true", "git push --force"):
            self.assertNotIn(unsafe, text)


    def test_workflow_depends_on_current_audited_v229_blob(self):
        """A safe V229 update must repin V235, not silently disable its SHA gate."""
        root = Path(__file__).resolve().parents[1]
        source = "scripts/boat_edge_v229_atomic_freeze.py"
        workflow = (root / ".github/workflows/V235.yml").read_text(encoding="utf-8")
        result = subprocess.run(
            ["git", "hash-object", source], cwd=root,
            capture_output=True, text=True, check=True,
        )
        current_sha = result.stdout.strip()
        self.assertEqual(len(current_sha), 40)
        self.assertIn(f"'{source}:{current_sha}'", workflow)
        self.assertIn("V234_PRE_RESULT_DEPENDENCY_CHANGED_$path", workflow)
        self.assertNotIn(
            f"{source}:c77d917ded93dc5584e990f769ced1ba108f8ed4",
            workflow,
        )


if __name__ == "__main__":
    unittest.main()
, header, re.M)
            self.assertEqual(len(crons), expected_cron_counts[name], name)
            schedules[name] = [
                (field_set(cron.split()[0], 59), field_set(cron.split()[1], 23))
                for cron in crons
                if len(cron.split()) == 5
            ]
            self.assertEqual(len(schedules[name]), len(crons), name)

        # Synthetic fixed deadlines match the first three real 2026-10-17
        # races. Test on the previous UTC calendar date (JST is UTC+09).
        for clock in ('08:35', '08:43', '08:51'):
            hour, minute = map(int, clock.split(':'))
            deadline = datetime(2026, 10, 17, hour, minute, tzinfo=JST)
            covered = {}
            for name, crons in schedules.items():
                matches = []
                for before in range(10, 1, -1):
                    instant = (deadline - timedelta(minutes=before)).astimezone(timezone.utc)
                    if any(instant.minute in mins and instant.hour in hours
                           for mins, hours in crons):
                        matches.append(instant.astimezone(JST).strftime('%H:%M'))
                covered[name] = matches
                self.assertTrue(matches, (clock, name, covered))
            # Existing direct first-Git-save owners, plus independent
            # PRE_RESULT sources, must retain planned opportunities.
            self.assertTrue(covered['v235'], clock)
            self.assertTrue(covered['v229'], clock)
            self.assertTrue(covered['v216'], clock)
            self.assertTrue(covered['collector'], clock)
            self.assertTrue(covered['official_odds'], clock)

    def test_v235_pinned_fast_lane_matches_main_git_blob(self):
        # Gate1C: Future V230 code changes MUST carry a reviewed V235 pin
        # update or fail PR CI before live pre-result collection/freeze.
        root=Path(__file__).resolve().parents[1]
        filename='scripts/boat_edge_v230_fast_lane.py'
        raw=(root/filename).read_bytes()
        git_blob=hashlib.sha1(b'blob '+str(len(raw)).encode('ascii')+b'\x00'+raw).hexdigest()
        workflow=(root/'.github/workflows/V235.yml').read_text(encoding='utf-8')
        self.assertIn(f"'{filename}:{git_blob}'",workflow)
        self.assertIn('test "$(git hash-object "$path")" = "$sha"',workflow)

    def test_window_does_not_invent_a_prediction(self):
        with tempfile.TemporaryDirectory() as base:
            root = Path(base)
            source(root)
            early = receipt(root, datetime(2026, 10, 14, 8, 10, tzinfo=JST))
            self.assertEqual(early["status"], "BEFORE_SOURCE_WINDOW")
            self.assertFalse(early["prediction_saved_proven"])
            self.assertEqual(early["race_key"], KEY)
            active = receipt(root, datetime(2026, 10, 14, 8, 28, tzinfo=JST))
            self.assertEqual(active["status"], "SOURCE_WINDOW_NO_SNAPSHOT")
            self.assertFalse(active["prediction_saved_proven"])

    def test_1r_priority_advances_to_next_race_after_deadline(self):
        with tempfile.TemporaryDirectory() as base:
            root = Path(base)
            source(root)
            catalog = json.loads((root / "data/today.json").read_text())
            catalog["venues"][0]["races"].append({
                "race_key": "20261014-14-02", "deadline": "09:01"})
            save(root, "data/today.json", catalog)
            before = datetime(2026, 10, 14, 8, 20, tzinfo=JST)
            after = datetime(2026, 10, 14, 8, 38, tzinfo=JST)
            self.assertEqual(choose(root, before)[1], KEY)
            self.assertEqual(choose(root, after)[1], "20261014-14-02")
            self.assertEqual(choose(root, after, requested=KEY)[1], KEY)

    def test_live_v230_target_wins_over_expired_two_minute_grace(self):
        # 2026-10-16 production regression: 10:30:32 receipt picked expired
        # Heiwajima 1R while V230 successfully froze Ashiya 5R (10:34).
        with tempfile.TemporaryDirectory() as base:
            root = Path(base)
            expired = "20261016-04-01"
            live = "20261016-21-05"
            save(root, "data/today.json", {
                "date": "2026-10-16", "venues": [
                    {"venue": "平和島", "races": [{"race_key": expired, "deadline": "10:30"}]},
                    {"venue": "芦屋", "races": [{"race_key": live, "deadline": "10:34"}]}
                ]})
            save(root, "data/site_autopilot/v230_fast_current.json", {
                "day_jst": "20261016", "targets": [live],
                "outcomes": {live: "fresh_verified"}})
            now = datetime(2026, 10, 16, 10, 30, 32, tzinfo=JST)
            self.assertEqual(choose(root, now)[1], live)
            self.assertEqual(receipt(root, now)["race_key"], live)
            self.assertEqual(choose(root, now, requested=expired)[1], expired)

    def test_no_v230_status_still_prefers_future_over_expired_grace(self):
        with tempfile.TemporaryDirectory() as base:
            root = Path(base)
            save(root, "data/today.json", {
                "date": "2026-10-16", "venues": [
                    {"venue": "平和島", "races": [
                        {"race_key": "20261016-04-01", "deadline": "10:30"},
                        {"race_key": "20261016-04-02", "deadline": "10:53"}]}
                ]})
            now = datetime(2026, 10, 16, 10, 30, 32, tzinfo=JST)
            self.assertEqual(choose(root, now)[1], "20261016-04-02")

    def test_local_only_not_a_git_commit(self):
        with tempfile.TemporaryDirectory() as base:
            root = Path(base)
            source(root)
            frozen(root)
            candidate = receipt(root, datetime(2026, 10, 14, 8, 29, tzinfo=JST))
            self.assertEqual(candidate["status"], "LOCAL_SNAPSHOT_NOT_FIRST_GIT_COMMITTED")
            self.assertFalse(candidate["prediction_saved_proven"])
            self.assertEqual(candidate["model_id"], "not_stored")
            self.assertEqual(candidate["prediction_kind"], "SITE_REFERENCE_V122")
            self.assertEqual(len(candidate["top10"]), 10)

    def test_exact_sha_first_added_commit_before_deadline(self):
        with tempfile.TemporaryDirectory() as base:
            root = Path(base)
            source(root)
            path = frozen(root)
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            subprocess.run(["git", "config", "user.name", "Test"], cwd=root, check=True)
            subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=root, check=True)
            subprocess.run(["git", "add", "data/today.json", "data/races",
                            "data/site_prediction_snapshots", "data/site_prediction_audit"],
                           cwd=root, check=True)
            env = os.environ.copy()
            env["GIT_AUTHOR_DATE"] = "2026-10-14T08:29:00+09:00"
            env["GIT_COMMITTER_DATE"] = "2026-10-14T08:29:00+09:00"
            subprocess.run(["git", "commit", "-qm", "prospective proof"], cwd=root,
                           env=env, check=True)
            result = receipt(root, datetime(2026, 10, 14, 8, 31, tzinfo=JST))
            self.assertEqual(result["status"], "SITE_FIRST_GIT_COMMIT_BEFORE_DEADLINE")
            self.assertTrue(result["prediction_saved_proven"])
            self.assertEqual(result["snapshot_sha256"], hashlib.sha256(path.read_bytes()).hexdigest())
            self.assertEqual(result["first_git_snapshot_sha256"], result["snapshot_sha256"])
            self.assertEqual(len(result["first_git_commit"]), 40)
            self.assertTrue(result["first_git_commit_at"].startswith("2026-10-14T08:29:00"))

    def test_git_first_commit_after_deadline_is_not_a_valid_save(self):
        with tempfile.TemporaryDirectory() as base:
            root = Path(base)
            source(root)
            frozen(root)
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            subprocess.run(["git", "config", "user.name", "Test"], cwd=root, check=True)
            subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=root, check=True)
            subprocess.run(["git", "add", "data/today.json", "data/races",
                            "data/site_prediction_snapshots", "data/site_prediction_audit"],
                           cwd=root, check=True)
            env = os.environ.copy()
            env["GIT_AUTHOR_DATE"] = "2026-10-14T08:36:00+09:00"
            env["GIT_COMMITTER_DATE"] = "2026-10-14T08:36:00+09:00"
            subprocess.run(["git", "commit", "-qm", "late publish not prospective"],
                           cwd=root, env=env, check=True)
            result = receipt(root, datetime(2026, 10, 14, 8, 37, tzinfo=JST))
            self.assertEqual(result["status"], "FIRST_GIT_COMMIT_NOT_SOURCE_BOUND_PREDEADLINE")
            self.assertFalse(result["prediction_saved_proven"])

    def test_audit_failure_fails_closed(self):
        with tempfile.TemporaryDirectory() as base:
            root = Path(base)
            source(root)
            frozen(root)
            save(root, f"data/site_prediction_audit/{KEY}.json", {
                "pass": True, "latest_snapshot_sha256": "0" * 64})
            result = receipt(root, datetime(2026, 10, 14, 8, 31, tzinfo=JST))
            self.assertEqual(result["status"], "SNAPSHOT_OR_V229_AUDIT_UNVERIFIED")
            self.assertFalse(result["prediction_saved_proven"])

    def test_v230_script_mode_requires_repo_root_pythonpath(self):
        # -m unittest from cwd implicitly sees the repo root, but executing
        # scripts/boat_edge_v230_fast_lane.py directly does not. Keep the
        # original safety-lock import resolvable in both V235 and V230 owners.
        root = Path(__file__).resolve().parents[1]
        commands = {
            ".github/workflows/V235.yml":
                "PYTHONPATH=.:scripts PYTHONDONTWRITEBYTECODE=1 python3 "
                "scripts/boat_edge_v230_fast_lane.py --workers 8 --retry-imminent",
            ".github/workflows/BOAT_EDGE_V230_FAST_OFFICIAL_PREDEADLINE.yml":
                "PYTHONPATH=.:scripts PYTHONDONTWRITEBYTECODE=1 python3 "
                "scripts/boat_edge_v230_fast_lane.py",
        }
        for path, command in commands.items():
            text = (root / path).read_text(encoding="utf-8")
            self.assertIn(command, text)
        env = dict(os.environ)
        env["PYTHONPATH"] = ".:scripts"
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        result = subprocess.run(
            [sys.executable, "scripts/boat_edge_v230_fast_lane.py", "--help"],
            cwd=root, env=env, capture_output=True, text=True, timeout=15,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("--retry-imminent", result.stdout)

    def test_workflow_has_0820_jst_owner_without_duplicate_writers(self):
        text = (Path(__file__).resolve().parents[1] /
                ".github/workflows/V235.yml").read_text(encoding="utf-8")
        self.assertIn("cron: '20 23 * * *'", text)
        self.assertIn("python3 scripts/boat_edge_v230_fast_lane.py --workers 8 --retry-imminent", text)
        self.assertNotIn("--priority-race-key 20261014-14-01", text)
        self.assertIn("python3 scripts/boat_edge_v232_pre_result_cohort.py", text)
        self.assertIn("python3 scripts/boat_edge_v235_predeadline_receipt.py", text)
        self.assertIn("V235_END_TO_END_SITE_PRE_RESULT_COHORT_VERIFIED", text)
        # A local predeadline snapshot is not proof of a timely first Git commit.
        self.assertIn("V235_TAKEOVER_CANDIDATE=1", text)
        self.assertIn("V235_TAKEOVER_FIRST_GIT_PROOF", text)
        self.assertIn("V235_FIRST_GIT_PROOF_REQUIRED_KEEP_V233", text)
        self.assertIn("if: ${{ !cancelled() }}", text)
        self.assertIn("env.write('V235_TAKEOVER_VERIFIED=1' + chr(10))", text)
        self.assertLess(text.index("V235_TAKEOVER_CANDIDATE=1"),
                        text.index("V235_TAKEOVER_FIRST_GIT_PROOF"))
        self.assertLess(text.index("V235_TAKEOVER_FIRST_GIT_PROOF"),
                        text.index("V235_TAKEOVER_VERIFIED=1' + chr(10)"))
        self.assertLess(text.index("V235_TAKEOVER_VERIFIED=1' + chr(10)"),
                        text.index("Disable obsolete V234 and V233"))
        self.assertIn("V235_KEEP_V233_UNTIL_NEW_PRE_RESULT_EVIDENCE_IS_COMMITTED", text)
        for unsafe in ("results_seen=true", "scoring=true", "git push --force"):
            self.assertNotIn(unsafe, text)


    def test_workflow_depends_on_current_audited_v229_blob(self):
        """A safe V229 update must repin V235, not silently disable its SHA gate."""
        root = Path(__file__).resolve().parents[1]
        source = "scripts/boat_edge_v229_atomic_freeze.py"
        workflow = (root / ".github/workflows/V235.yml").read_text(encoding="utf-8")
        result = subprocess.run(
            ["git", "hash-object", source], cwd=root,
            capture_output=True, text=True, check=True,
        )
        current_sha = result.stdout.strip()
        self.assertEqual(len(current_sha), 40)
        self.assertIn(f"'{source}:{current_sha}'", workflow)
        self.assertIn("V234_PRE_RESULT_DEPENDENCY_CHANGED_$path", workflow)
        self.assertNotIn(
            f"{source}:c77d917ded93dc5584e990f769ced1ba108f8ed4",
            workflow,
        )


if __name__ == "__main__":
    unittest.main()
