import unittest
from datetime import datetime, timezone, timedelta
from scripts.boat_edge_v251_pages_recovery import decision, PAGE_PATH

NOW = datetime(2026, 10, 12, 3, 0, tzinfo=timezone.utc)
SHA = 'a' * 40
OLD = 'b' * 40

def iso(minutes):
    return (NOW + timedelta(minutes=minutes)).isoformat()

def normal():
    pages = {'build_type': 'legacy', 'source': {'branch': 'main'}}
    commit = {'sha': SHA, 'commit': {'committer': {'date': iso(-25)}}}
    runs = [{'path': PAGE_PATH, 'conclusion': 'cancelled', 'status': 'completed',
             'created_at': iso(-10), 'head_sha': SHA},
            {'path': PAGE_PATH, 'conclusion': 'success', 'status': 'completed',
             'created_at': iso(-45), 'updated_at': iso(-40), 'head_sha': OLD}]
    return pages, commit, runs


class V251PublishRecovery(unittest.TestCase):
    def test_stale_cancelled_pages_eligible_only_after_quiet_window(self):
        self.assertEqual(decision(*normal(), now=NOW), 'REQUEST_LEGACY_PAGES_BUILD')

    def test_published_head_skips(self):
        p,c,r = normal()
        r[0].update(conclusion='success')
        self.assertEqual(decision(p,c,r,now=NOW),'CURRENT_COMMIT_PUBLISHED')

    def test_older_sha_success_cannot_hide_unpublished_main_for_seven_minutes(self):
        p,c,r = normal()
        r[1]['updated_at'] = iso(-7)
        self.assertNotEqual(r[1]['head_sha'], c['sha'])
        self.assertEqual(decision(p,c,r,now=NOW),'REQUEST_LEGACY_PAGES_BUILD')

    def test_very_recent_other_sha_success_still_gets_brief_grace(self):
        p,c,r = normal()
        r[1]['updated_at'] = iso(-2)
        self.assertNotEqual(r[1]['head_sha'], c['sha'])
        self.assertEqual(decision(p,c,r,now=NOW),'RECENT_PAGES_SUCCESS_GRACE')

    def test_active_pages_skip(self):
        p,c,r = normal()
        r[0]['status'] = 'in_progress'
        r[0]['conclusion'] = None
        self.assertEqual(decision(p,c,r,now=NOW),'PAGES_BUILD_ALREADY_ACTIVE')

    def test_recent_commit_skip(self):
        p,c,r = normal()
        c['commit']['committer']['date'] = iso(-2)
        self.assertEqual(decision(p,c,r,now=NOW),'HEAD_STILL_CHANGING')

    def test_wrong_source_skip(self):
        p,c,r = normal()
        p['source']['branch'] = 'gh-pages'
        self.assertEqual(decision(p,c,r,now=NOW),'PAGES_SOURCE_NOT_MAIN')

    def test_workflow_pages_skip(self):
        p,c,r = normal()
        p['build_type'] = 'workflow'
        self.assertEqual(decision(p,c,r,now=NOW),'NOT_BRANCH_BASED_PAGES')

    def test_no_credible_runs_skip(self):
        p,c,r = normal()
        self.assertEqual(decision(p,c,[],now=NOW),'NO_PAGES_RUN_EVIDENCE')

    def test_unverified_commit_sha_skip(self):
        p,c,r = normal()
        c['sha'] = 'invalid'
        self.assertEqual(decision(p,c,r,now=NOW),'INVALID_HEAD')

    def test_invalid_commit_time_skip(self):
        p,c,r = normal()
        c['commit']['committer']['date'] = ''
        self.assertEqual(decision(p,c,r,now=NOW),'HEAD_TIME_UNVERIFIED')

    def test_recent_build_quiet_window_skip(self):
        p,c,r = normal()
        r[0]['created_at'] = iso(-1)
        self.assertEqual(decision(p,c,r,now=NOW),'RECENT_PAGE_BUILD_WAIT')


if __name__ == '__main__':
    unittest.main()
