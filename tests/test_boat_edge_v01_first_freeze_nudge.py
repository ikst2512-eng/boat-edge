"""Offline regression for the existing-V229 source-commit nudge (never hits GitHub)."""
from __future__ import annotations
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/boat_edge_v01_first_freeze_nudge.sh"
FREEZE = "BOAT_EDGE_V229_ATOMIC_FREEZE_AUDIT.yml"

def create_stub(folder: Path, name: str, text: str) -> None:
    p = folder / name
    p.write_text("#!/usr/bin/env bash\nset -euo pipefail\n" + text + "\n", encoding="utf-8")
    p.chmod(0o755)

class SourceCommitV229Nudge(unittest.TestCase):
    def run_case(self, plan=None, runs=None, **changes):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            bin_dir = root / "bin"
            bin_dir.mkdir()
            create_stub(bin_dir, "date", '''
if [[ -n "$MOCK_NOW_EPOCH" ]]; then
  if [[ -f "$MOCK_SLEPT" ]]; then printf '%s\n' "$MOCK_AFTER_EPOCH"
  else printf '%s\n' "$MOCK_NOW_EPOCH"; fi
else /usr/bin/date "$@"; fi
''')
            create_stub(bin_dir, "sleep", '''
printf 'sleep:%s\n' "$*" >> "$MOCK_EVENTS"
touch "$MOCK_SLEPT"
''')
            create_stub(bin_dir, "git", 'printf "git:%s\\n" "$*" >> "$MOCK_EVENTS"')
            create_stub(bin_dir, "python3", '''
if [[ "${MOCK_PYTHON_FAIL:-0}" == 1 ]]; then exit 1; fi
if [[ -f "$MOCK_SLEPT" && -n "$MOCK_PLAN_AFTER_SLEEP" ]]; then
  printf '%s\n' "$MOCK_PLAN_AFTER_SLEEP"
else
  printf '%s\n' "$MOCK_PLAN"
fi
''')
            create_stub(bin_dir, "gh", '''
if [[ "$1" == api ]]; then
  if [[ "${MOCK_GH_FAIL:-0}" == 1 ]]; then exit 1; fi
  if [[ -f "$MOCK_SLEPT" && -n "$MOCK_RUNS_AFTER_SLEEP" ]]; then
    printf '%s\n' "$MOCK_RUNS_AFTER_SLEEP"
  else
    printf '%s\n' "$MOCK_RUNS"
  fi
elif [[ "$1" == workflow && "$2" == run ]]; then
  printf "dispatch:%s\\n" "$*" >> "$MOCK_EVENTS"
else
  exit 2
fi
''')
            events = root / "events"
            env = {
                **os.environ, "PATH": str(bin_dir) + os.pathsep + os.environ["PATH"],
                "GITHUB_REPOSITORY": "ikst2512-eng/boat-edge",
                "GITHUB_REF": "refs/heads/main", "GH_TOKEN": "unit-test-token",
                "MOCK_EVENTS": str(events),
                "MOCK_SLEPT": str(root / "slept"),
                "MOCK_NOW_EPOCH": "",
                "MOCK_AFTER_EPOCH": "",
                "MOCK_PLAN_AFTER_SLEEP": "",
                "MOCK_RUNS_AFTER_SLEEP": "",
                "MOCK_PLAN": json.dumps({"workflows": [FREEZE]} if plan is None else plan),
                "MOCK_RUNS": json.dumps({"workflow_runs": []} if runs is None else runs),
            }
            env.update({k: str(v) for k, v in changes.items()})
            proc = subprocess.run(["bash", str(SCRIPT)], cwd=root, env=env,
                                  capture_output=True, text=True, timeout=10)
            actions = events.read_text(encoding="utf-8") if events.exists() else ""
            self.assertEqual(proc.returncode, 0, (proc.stdout, proc.stderr))
            return proc.stdout, actions

    @unittest.skipUnless(shutil.which("jq"), "jq required for production workflow")
    def test_dispatch_only_one_existing_owner(self):
        output, events = self.run_case()
        self.assertIn("EXISTING_V229_DISPATCHED", output)
        self.assertEqual(events.count("dispatch:"), 1)
        self.assertIn("workflow run " + FREEZE + " --ref main", events)
        self.assertNotIn("site-odds.yml", events)

    @unittest.skipUnless(shutil.which("jq"), "jq required for production workflow")
    def test_empty_or_wrong_plan_never_dispatches(self):
        for plan in ({"workflows": []}, {"workflows": ["site-odds.yml"]}, {"workflows": "bad"}):
            _, events = self.run_case(plan=plan)
            self.assertNotIn("dispatch:", events)

    @unittest.skipUnless(shutil.which("jq"), "jq required for production workflow")
    def test_queued_cooldown_and_malformed_api_fail_closed(self):
        now = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
        cases = [
            {"workflow_runs": [{"status": "in_progress", "created_at": now}]},
            {"workflow_runs": [{"status": "completed", "created_at": now}]},
            {"error": "malformed"},
        ]
        for data in cases:
            _, events = self.run_case(runs=data)
            self.assertNotIn("dispatch:", events)

    @unittest.skipUnless(shutil.which("jq"), "jq required for production workflow")
    def test_skipped_cancelled_v229_without_a_job_cannot_consume_cooldown(self):
        # A completed no-job Actions event is not a first-Git-save attempt.
        # Preserve the existing 2-10 minute source window and active-run gate.
        epoch = 1800000000
        stamp = datetime.fromtimestamp(epoch - 15, timezone.utc).isoformat(
            timespec="seconds").replace("+00:00", "Z")
        for conclusion in ("skipped", "cancelled"):
            with self.subTest(conclusion=conclusion):
                output, events = self.run_case(
                    runs={"workflow_runs": [{"status": "completed",
                        "conclusion": conclusion, "created_at": stamp}]},
                    MOCK_NOW_EPOCH=epoch)
                self.assertIn("EXISTING_V229_DISPATCHED", output)
                self.assertEqual(events.count("dispatch:"), 1)
                self.assertEqual(events.count("sleep:"), 0)

        # Mixed skipped/cancelled completions do not suppress a real attempt.
        # The real V229 success must still enforce its full 120-second cooldown,
        # with exactly one bounded recheck before an eventual dispatch.
        real = datetime.fromtimestamp(epoch - 75, timezone.utc).isoformat(
            timespec="seconds").replace("+00:00", "Z")
        ignored = [
            {"status": "completed", "conclusion": conclusion, "created_at": stamp}
            for conclusion in ("skipped", "cancelled")
        ]
        rows = {"workflow_runs": ignored + [
            {"status": "completed", "conclusion": "success", "created_at": real}
        ]}
        output, events = self.run_case(
            runs=rows, MOCK_NOW_EPOCH=epoch, MOCK_AFTER_EPOCH=epoch + 47)
        self.assertIn("BOUNDED_WAIT seconds=47", output)
        self.assertIn("EXISTING_V229_DISPATCHED", output)
        self.assertEqual(events.count("sleep:"), 1)
        self.assertEqual(events.count("dispatch:"), 1)
        self.assertGreaterEqual(events.count("git:fetch"), 2)

        # Failed but actually attempted runs continue consuming the cooldown.
        output, events = self.run_case(
            runs={"workflow_runs": [{"status": "completed",
                "conclusion": "failure", "created_at": stamp}]},
            MOCK_NOW_EPOCH=epoch, MOCK_AFTER_EPOCH=epoch + 110)
        self.assertIn("V229_COOLDOWN", output)
        self.assertNotIn("dispatch:", events)

    @unittest.skipUnless(shutil.which("jq"), "jq required for production workflow")
    def test_bounded_existing_cooldown_recheck_then_single_v229_dispatch(self):
        # A V229 run 65 seconds ago can have missed the odds published after
        # it finished. Keep the full 120s, re-read main and exact 2-10m source
        # gate, and dispatch at most one EXISTING V229 writer.
        epoch = 1800000000
        stamp = datetime.fromtimestamp(epoch - 65, timezone.utc).isoformat(
            timespec="seconds").replace("+00:00", "Z")
        rows = {"workflow_runs": [{"status": "completed",
                                  "conclusion": "success", "created_at": stamp}]}
        clock = dict(MOCK_NOW_EPOCH=epoch, MOCK_AFTER_EPOCH=epoch + 58)
        output, events = self.run_case(runs=rows, **clock)
        self.assertIn("BOUNDED_WAIT seconds=57", output)
        self.assertEqual(events.count("sleep:"), 1)
        self.assertEqual(events.count("dispatch:"), 1)
        self.assertGreaterEqual(events.count("git:fetch"), 2)
        self.assertIn("EXISTING_V229_DISPATCHED", output)
        # A changed/expired source window MUST block the second attempt.
        output, events = self.run_case(
            runs=rows, MOCK_PLAN_AFTER_SLEEP=json.dumps({"workflows": []}),
            **clock)
        self.assertIn("NOT_SOURCE_READY_OR_OUTSIDE_WINDOW", output)
        self.assertEqual(events.count("dispatch:"), 0)
        # Another V229 starts while waiting; do not send a second one.
        output, events = self.run_case(
            runs=rows, MOCK_RUNS_AFTER_SLEEP=json.dumps({"workflow_runs": [
                {"status": "in_progress", "created_at": stamp}]}),
            **clock)
        self.assertIn("V229_ALREADY_ACTIVE", output)
        self.assertEqual(events.count("dispatch:"), 0)

    @unittest.skipUnless(shutil.which("jq"), "jq required for production workflow")
    def test_second_recent_completed_v229_never_starts_another_wait(self):
        # A new completed V229 can land during the first bounded hold. In
        # that case the same nudge must NOT begin another wait/loop. The
        # child bash must inherit the once-only marker across exec.
        initial = 1800000000
        first = datetime.fromtimestamp(initial - 65, timezone.utc).isoformat(
            timespec="seconds").replace("+00:00", "Z")
        latest = datetime.fromtimestamp(initial + 20, timezone.utc).isoformat(
            timespec="seconds").replace("+00:00", "Z")
        output, events = self.run_case(
            runs={"workflow_runs": [{"status": "completed", "conclusion":
                                     "success", "created_at": first}]},
            MOCK_RUNS_AFTER_SLEEP=json.dumps({"workflow_runs": [
                {"status": "completed", "conclusion": "success",
                 "created_at": latest}]}),
            MOCK_NOW_EPOCH=initial, MOCK_AFTER_EPOCH=initial + 58)
        self.assertIn("BOUNDED_WAIT seconds=57", output)
        self.assertIn("V229_COOLDOWN", output)
        self.assertEqual(events.count("sleep:"), 1)
        self.assertEqual(events.count("dispatch:"), 0)

    @unittest.skipUnless(shutil.which("jq"), "jq required for production workflow")
    def test_no_hold_when_v229_cooldown_is_longer_than_90_seconds(self):
        epoch = 1800000000
        stamp = datetime.fromtimestamp(epoch - 10, timezone.utc).isoformat(
            timespec="seconds").replace("+00:00", "Z")
        output, events = self.run_case(
            runs={"workflow_runs": [{"status": "completed",
                "conclusion": "success", "created_at": stamp}]},
            MOCK_NOW_EPOCH=epoch, MOCK_AFTER_EPOCH=epoch + 115)
        self.assertIn("V229_COOLDOWN", output)
        self.assertEqual(events.count("sleep:"), 0)
        self.assertEqual(events.count("dispatch:"), 0)

    @unittest.skipUnless(shutil.which("jq"), "jq required for production workflow")
    def test_untrusted_missing_auth_and_unavailable_evidence_fail_closed(self):
        for changes in (
            {"GITHUB_REF": "refs/pull/1/merge"},
            {"GITHUB_REPOSITORY": "attacker/fork"},
            {"GH_TOKEN": ""},
            {"MOCK_PYTHON_FAIL": "1"},
            {"MOCK_GH_FAIL": "1"},
        ):
            _, events = self.run_case(**changes)
            self.assertNotIn("dispatch:", events)

    def test_v71_official_odds_prioritizes_live_freeze_window_without_new_writer(self):
        # Execute only the local race-selection block: no HTTP, Git or dispatch.
        # The collector produces one final index and retains the original 120
        # odds validation and publication stage untouched.
        import re
        import textwrap
        from datetime import timedelta
        wf = (SCRIPT.parents[1] / ".github/workflows/site-odds.yml").read_text(encoding="utf-8")
        self.assertEqual(wf.count("          races=[]\n"), 1)
        block = wf.split("          races=[]\n", 1)[1].split(
            "          session=requests.Session()", 1)[0]
        code = "races=[]\n" + textwrap.dedent(block)
        at = datetime(2026, 10, 16, 6, 42, tzinfo=timezone.utc).astimezone(
            timezone(timedelta(hours=9)))
        rows = [
            ("20261016-24-03", 3, "16:21"),  # 39m, original first venue
            ("20261016-24-02", 2, "15:47"),  # 5m, urgent
            ("20261016-02-11", 11, "15:51"), # 9m, urgent
            ("20261016-02-10", 10, "15:41"), # past deadline, still in V71
            ("20261016-20-03", 3, "15:58"),  # 16m, next-up
            ("20261016-20-02", 2, "15:43"),  # 1m, outside strict freeze
        ]
        catalog = {"venues": [
            {"jcd": key.split("-")[1], "races": [
                {"race_key": key, "race_no": no, "deadline": deadline}]}
            for key, no, deadline in rows
        ]}
        namespace = {"today": catalog, "now": at, "re": re}
        exec(compile(code, "site-odds:race-selector", "exec"), namespace)
        ordered = [row["race_key"] for row in namespace["races"]]
        self.assertEqual(ordered, [
            "20261016-24-02", "20261016-02-11",
            "20261016-20-03", "20261016-24-03",
            "20261016-20-02", "20261016-02-10"
        ])
        self.assertIn("verify_official_dom_price_mapping(html)", wf)
        self.assertIn('if len(odds) != 120 or unavailable:', wf)
        self.assertIn("V71_SOURCE_TIMESTAMP_GUARDED_ODDS_PUBLISHED", wf)
        self.assertIn("Nudge existing V229 from successfully published PRE_RESULT inputs", wf)

    def test_v71_only_trusted_main_may_write_odds_or_dispatch(self):
        # A 2026-10-16 feature-branch push ran V71 and wrote to origin/main,
        # despite the downstream nudge correctly refusing the branch. Gate
        # the WHOLE odds job before fetching, resetting or publishing source.
        wf = (SCRIPT.parents[1] / ".github/workflows/site-odds.yml").read_text(encoding="utf-8")
        header = wf.split("concurrency:", 1)[0]
        job = wf.split("jobs:", 1)[1].split("steps:", 1)[0]
        self.assertIn("    branches: [main]", header)
        self.assertIn("github.ref == 'refs/heads/main'", job)
        self.assertIn("github.repository == 'ikst2512-eng/boat-edge'", job)
        self.assertIn("workflow_dispatch:", header)  # dispatch still needs job guard
        self.assertIn("git reset --hard origin/main", wf)
        self.assertIn("git push origin HEAD:main", wf)
        self.assertIn("Nudge existing V229 from successfully published PRE_RESULT inputs", wf)

    def test_shell_and_workflow_contract(self):
        p = subprocess.run(["bash", "-n", str(SCRIPT)], capture_output=True, text=True)
        self.assertEqual(p.returncode, 0, p.stderr)
        for name in ("site-odds.yml", "auto-update.yml"):
            wf = (SCRIPT.parents[1] / ".github/workflows" / name).read_text(encoding="utf-8")
            self.assertIn("Nudge existing V229 from successfully published PRE_RESULT inputs", wf)
            self.assertIn("bash scripts/boat_edge_v01_first_freeze_nudge.sh", wf)
            self.assertIn("actions: write", wf)
        # This nudge never runs a scorer or writes a new snapshot itself.
        script = SCRIPT.read_text(encoding="utf-8")
        self.assertIn("--recovery-plan", script)
        self.assertIn("workflow run", script)
        self.assertNotIn("git push", script)
        self.assertNotIn("result/payout", script.lower())

if __name__ == "__main__":
    unittest.main()
