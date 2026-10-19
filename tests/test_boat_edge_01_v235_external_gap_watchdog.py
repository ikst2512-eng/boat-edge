"""No networking or GitHub writes: synthetic external-watchdog safety tests."""
import importlib.util
from datetime import datetime, timezone
from pathlib import Path
import unittest
from unittest.mock import patch

P = Path(__file__).resolve().parents[1] / 'scripts' / 'boat_edge_01_v235_external_gap_watchdog.py'
spec = importlib.util.spec_from_file_location('edge_v235_external', P)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
NOW = datetime(2026, 10, 16, 1, 40, tzinfo=timezone.utc)  # 10:40 JST


def fixture():
    return {'date': '2026-10-16', 'venues': [
        {'races': [{'race_key': '20261016-02-01', 'deadline': '10:47'},
                   {'race_key': '20261016-21-05', 'deadline': '10:34'},
                   {'race_key': '20261015-10-01', 'deadline': '10:48'}]}]}


def runs(status='completed', conclusion='success', created='2026-10-16T01:20:00Z'):
    return {'workflow_runs': [{'head_branch': 'main', 'status': status,
                               'conclusion': conclusion, 'created_at': created}]}


class WatchdogContract(unittest.TestCase):
    def setUp(self):
        self.workflow = {'path': '.github/workflows/V235.yml', 'state': 'active'}

    def test_only_future_same_day_4_to_19_minute_window(self):
        self.assertEqual(mod.imminent(fixture(), NOW), ['20261016-02-01'])
        x = fixture()
        x['date'] = '2026-10-15'
        self.assertEqual(mod.imminent(x, NOW), [])
        self.assertEqual(mod.imminent(
            fixture(), datetime(2026, 10, 16, 1, 44, tzinfo=timezone.utc)), [])

    def test_stale_real_run_may_recover_using_existing_v235(self):
        d = mod.decision(fixture(), self.workflow, runs(), NOW)
        self.assertTrue(d['dispatch'])
        self.assertEqual(d['targets'], ['20261016-02-01'])

    def test_recent_actual_run_blocks(self):
        d = mod.decision(fixture(), self.workflow,
                         runs(created='2026-10-16T01:37:00Z'), NOW)
        self.assertEqual(d['reason'], 'V235_RECENT_ACTUAL_RUN')
        self.assertFalse(d['dispatch'])

    def test_skipped_does_not_fake_success_or_cooldown(self):
        d = mod.decision(fixture(), self.workflow,
                         runs(conclusion='skipped', created='2026-10-16T01:39:00Z'), NOW)
        self.assertTrue(d['dispatch'])

    def test_queued_or_running_blocks_even_when_old(self):
        for state in ('queued', 'in_progress', 'pending', 'waiting', 'requested'):
            with self.subTest(state=state):
                d = mod.decision(fixture(), self.workflow,
                                 runs(status=state, conclusion=None), NOW)
                self.assertEqual(d['reason'], 'V235_ALREADY_ACTIVE')

    def test_unknown_workflow_and_empty_history_fail_closed(self):
        for w in ({'path': '.github/workflows/V235.yml', 'state': 'disabled_manually'},
                  {'path': '.github/workflows/other.yml', 'state': 'active'}):
            self.assertFalse(mod.decision(fixture(), w, runs(), NOW)['dispatch'])
        self.assertFalse(mod.decision(fixture(), self.workflow,
                                      {'workflow_runs': []}, NOW)['dispatch'])
        self.assertFalse(mod.decision(fixture(), self.workflow,
                                      runs(status='mystery'), NOW)['dispatch'])

    def test_only_other_branches_history_never_authorizes_main_dispatch(self):
        # GitHub's API can return runs but none for main. This is a history
        # coverage gap, NOT evidence that the main V235 workflow is idle.
        alien = runs()
        alien['workflow_runs'][0]['head_branch'] = 'feature/test'
        d = mod.decision(fixture(), self.workflow, alien, NOW)
        self.assertFalse(d['dispatch'])
        self.assertEqual(d['reason'], 'NO_MAIN_V235_RUN_HISTORY')

    def test_skipped_main_record_still_distinct_from_nonmain_history(self):
        sample = runs(conclusion='skipped', created='2026-10-16T01:39:00Z')
        other = runs(created='2026-10-16T01:39:00Z')['workflow_runs'][0]
        other['head_branch'] = 'feature/test'
        sample['workflow_runs'].append(other)
        d = mod.decision(fixture(), self.workflow, sample, NOW)
        self.assertTrue(d['dispatch'])

    def test_clock_or_run_time_ambiguity_blocks(self):
        for t in ('2026-10-16T01:45:00Z', 'garbled'):
            self.assertFalse(mod.decision(
                fixture(), self.workflow, runs(created=t), NOW)['dispatch'])

    def test_real_toda10_missed_window_replay_no_early_or_late_dispatch(self):
        # 2026-10-16 JST: original official source/scratch/120 odds were on
        # main by 15:05:52, but the V235 runs started at 15:03:41 and
        # 15:16:29, on either side of Toda 10R's 15:08-15:16 freeze window.
        # This is a SYNTHETIC decision replay, not proof an external host ran.
        catalog = {'date': '2026-10-16', 'venues': [
            {'races': [{'race_key': '20261016-02-10', 'deadline': '15:18'}]}]}
        history = runs(created='2026-10-16T06:03:41Z')
        def at(clock):
            return datetime.fromisoformat('2026-10-16T' + clock + '+00:00')
        # The existing 420s anti-duplicate guard must stay intact.
        self.assertEqual(
            mod.decision(catalog, self.workflow, history, at('06:08:00'))['reason'],
            'V235_RECENT_ACTUAL_RUN')
        # At 15:12 JST there are six minutes to deadline, the last
        # V235 was >7m ago, and the already-reviewed watchdog can dispatch.
        eligible = mod.decision(catalog, self.workflow, history, at('06:12:00'))
        self.assertTrue(eligible['dispatch'], eligible)
        self.assertEqual(eligible['reason'], 'MISSED_V235_RUNTIME_WITH_IMMINENT_RACE')
        self.assertEqual(eligible['targets'], ['20261016-02-10'])
        # Never stack duplicate jobs, even during an observable gap.
        active = runs(status='in_progress', conclusion=None,
                      created='2026-10-16T06:11:00Z')
        self.assertEqual(
            mod.decision(catalog, self.workflow, active, at('06:12:00'))['reason'],
            'V235_ALREADY_ACTIVE')
        # The external prewarm policy is 4-19m, NOT a late freeze bypass.
        self.assertEqual(
            mod.decision(catalog, self.workflow, history, at('06:15:00'))['reason'],
            'NO_SAME_DAY_PREWARM_RACE')

    def test_cancelled_zero_job_workflow_does_not_fake_runtime_cooldown(self):
        # Actual GitHub run 39185539407 on 2026-10-19 was cancelled
        # with zero jobs; a workflow-level cancellation is not source IO.
        record = runs(conclusion='cancelled', created='2026-10-16T01:39:00Z')
        record['workflow_runs'][0]['id'] = 39185539407
        fetched = []
        def lookup(run_id):
            fetched.append(run_id)
            return {'total_count': 0, 'jobs': []}
        d = mod.decision(fixture(), self.workflow, record, NOW, cancelled_jobs=lookup)
        self.assertTrue(d['dispatch'], d)
        self.assertEqual(fetched, [39185539407])

    def test_cancelled_with_any_job_keeps_cooldown(self):
        record = runs(conclusion='cancelled', created='2026-10-16T01:39:00Z')
        record['workflow_runs'][0]['id'] = 123456
        d = mod.decision(fixture(), self.workflow, record, NOW,
                         cancelled_jobs=lambda run_id: {
                             'total_count': 1,
                             'jobs': [{'id': 99, 'conclusion': 'cancelled'}]})
        self.assertFalse(d['dispatch'])
        self.assertEqual(d['reason'], 'V235_RECENT_ACTUAL_RUN')

    def test_cancelled_unverified_job_evidence_never_dispatches(self):
        record = runs(conclusion='cancelled', created='2026-10-16T01:39:00Z')
        record['workflow_runs'][0]['id'] = 123456
        for lookup in (None, lambda _: {'jobs': []},
                       lambda _: {'total_count': 1, 'jobs': []},
                       lambda _: {'total_count': 0, 'jobs': [{'id': 1}]},
                       lambda _: (_ for _ in ()).throw(RuntimeError('api failure'))):
            with self.subTest(lookup=lookup):
                d = mod.decision(fixture(), self.workflow, record, NOW,
                                 cancelled_jobs=lookup)
                # Positive count and zero jobs is unverified pagination.
                self.assertFalse(d['dispatch'])
        record['workflow_runs'][0].pop('id')
        self.assertEqual(mod.decision(fixture(), self.workflow, record, NOW,
                         cancelled_jobs=lambda _: {'total_count': 0, 'jobs': []})['reason'],
                         'V235_CANCELLED_JOBS_UNVERIFIED')

    def test_live_cancelled_zero_job_queries_exact_job_api_once(self):
        import base64
        import json
        encoded = base64.b64encode(json.dumps(fixture()).encode()).decode()
        record = runs(conclusion='cancelled', created='2026-10-16T01:39:00Z')
        record['workflow_runs'][0]['id'] = 39185539407
        seen = []
        def api(method, route, token, body=None):
            seen.append((method, route))
            if method == 'POST':
                return {}
            if '/contents/' in route:
                return {'encoding': 'base64', 'content': encoded}
            if '/jobs?' in route:
                return {'total_count': 0, 'jobs': []}
            if '/runs?' in route:
                return record
            return self.workflow
        with patch.dict(mod.os.environ,
                        {'BOAT_EDGE_GITHUB_ACTIONS_TOKEN': 'fixture',
                         'BOAT_EDGE_EXTERNAL_V235_ENABLED': 'true'}, clear=True), \
             patch.object(mod, 'api_json', side_effect=api), \
             patch.object(mod, 'utc_now', return_value=NOW):
            self.assertEqual(mod.main(['--live']), 0)
        self.assertEqual([x for x in seen if '/jobs?' in x[1]],
                         [('GET', '/actions/runs/39185539407/jobs?per_page=100')])
        self.assertEqual([x for x in seen if x[0] == 'POST'],
                         [('POST', '/actions/workflows/V235.yml/dispatches')])

    def test_dry_run_does_not_post_even_when_eligible(self):
        import base64
        import json
        encoded = base64.b64encode(json.dumps(fixture()).encode()).decode()

        def get(method, route, token, body=None):
            self.assertEqual(method, 'GET')
            if '/contents/' in route:
                return {'encoding': 'base64', 'content': encoded}
            if '/runs?' in route:
                return runs()
            return self.workflow

        with patch.object(mod, 'api_json', side_effect=get), \
             patch.object(mod, 'utc_now', return_value=NOW):
            self.assertEqual(mod.main([]), 0)

    def test_live_requires_token_before_any_io(self):
        with patch.dict(mod.os.environ, {'BOAT_EDGE_EXTERNAL_V235_ENABLED': 'true'}, clear=True), \
             patch.object(mod, 'api_json') as io:
            self.assertEqual(mod.main(['--live']), 2)
            io.assert_not_called()

    def test_blueprint_off_without_token_is_clean_noop(self):
        # The new paid Render Cron begins OFF and without any GitHub token.
        # It must not produce recurring failed runs, call GitHub, or dispatch.
        with patch.dict(mod.os.environ, {'BOAT_EDGE_EXTERNAL_V235_ENABLED': 'false'}, clear=True), \
             patch.object(mod, 'api_json') as io:
            self.assertEqual(mod.main(['--live']), 0)
            io.assert_not_called()

    def test_paid_scheduler_live_requires_separate_owner_enable_even_with_token(self):
        with patch.dict(mod.os.environ,
                        {'BOAT_EDGE_GITHUB_ACTIONS_TOKEN': 'fixture',
                         'BOAT_EDGE_EXTERNAL_V235_ENABLED': 'false'}, clear=True), \
             patch.object(mod, 'api_json') as io:
            self.assertEqual(mod.main(['--live']), 0)
            io.assert_not_called()

    def test_only_single_exact_dispatch_path(self):
        import base64
        import json
        encoded = base64.b64encode(json.dumps(fixture()).encode()).decode()
        seen = []

        def api(method, route, token, body=None):
            seen.append((method, route, body))
            if method == 'POST':
                return {}
            if '/contents/' in route:
                return {'encoding': 'base64', 'content': encoded}
            if '/runs?' in route:
                return runs()
            return self.workflow

        with patch.dict(mod.os.environ,
                        {'BOAT_EDGE_GITHUB_ACTIONS_TOKEN': 'fixture',
                         'BOAT_EDGE_EXTERNAL_V235_ENABLED': 'true'}, clear=True), \
             patch.object(mod, 'api_json', side_effect=api), \
             patch.object(mod, 'utc_now', return_value=NOW):
            self.assertEqual(mod.main(['--live']), 0)
        self.assertEqual([x for x in seen if x[0] == 'POST'], [
            ('POST', '/actions/workflows/V235.yml/dispatches', {'ref': 'main'})
        ])


if __name__ == '__main__':
    unittest.main()
