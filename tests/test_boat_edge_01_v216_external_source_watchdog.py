"""Offline, result-free tests for optional V216 source-ready observer backup."""
import base64
from datetime import datetime,timezone
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import boat_edge_01_v216_external_source_watchdog as v216
import boat_edge_01_external_cron as combo

NOW=datetime(2026,10,16,1,40,tzinfo=timezone.utc)  # 10:40 Japan
WORKFLOW={'path':'.github/workflows/BOAT_EDGE_V216_SOURCE_DIAGNOSTIC.yml','state':'active'}
CATALOG={'date':'2026-10-16','venues':[{'races':[
    {'race_key':'20261016-02-01','deadline':'10:47'},
    {'race_key':'20261015-02-01','deadline':'10:47'}]}]}


def runs(*,at='2026-10-16T01:20:00Z',status='completed',
         conclusion='success',branch='main'):
    return {'workflow_runs':[{'head_branch':branch,'created_at':at,
                              'status':status,'conclusion':conclusion}]}


class V216BackupContracts(unittest.TestCase):
    def test_stale_main_run_can_observe_real_imminent_source(self):
        s=v216.decision(CATALOG,WORKFLOW,runs(),NOW)
        self.assertTrue(s['dispatch'])
        self.assertEqual(s['targets'],['20261016-02-01'])

    def test_recent_real_execution_blocks(self):
        s=v216.decision(CATALOG,WORKFLOW,runs(at='2026-10-16T01:38:00Z'),NOW)
        self.assertFalse(s['dispatch'])
        self.assertEqual(s['reason'],'V216_RECENT_ACTUAL_RUN')

    def test_skip_does_not_imply_observation(self):
        s=v216.decision(CATALOG,WORKFLOW,
                        runs(conclusion='skipped',at='2026-10-16T01:39:00Z'),NOW)
        self.assertTrue(s['dispatch'])

    def test_active_or_unverified_never_dispatches(self):
        for status in ('queued','in_progress','waiting','requested','pending','mystery'):
            with self.subTest(status=status):
                self.assertFalse(v216.decision(
                    CATALOG,WORKFLOW,runs(status=status),NOW)['dispatch'])
        self.assertFalse(v216.decision(CATALOG,WORKFLOW,runs(at='bad'),NOW)['dispatch'])
        self.assertFalse(v216.decision(
            CATALOG,WORKFLOW,runs(at='2026-10-16T01:50:00Z'),NOW)['dispatch'])

    def test_wrong_workflow_wrong_branch_or_no_history_fails_closed(self):
        self.assertFalse(v216.decision(
            CATALOG,{'path':'.github/workflows/V235.yml','state':'active'},
            runs(),NOW)['dispatch'])
        self.assertFalse(v216.decision(
            CATALOG,{**WORKFLOW,'state':'disabled_manually'},runs(),NOW)['dispatch'])
        self.assertFalse(v216.decision(
            CATALOG,WORKFLOW,runs(branch='feature'),NOW)['dispatch'])
        self.assertFalse(v216.decision(
            CATALOG,WORKFLOW,{'workflow_runs':[]},NOW)['dispatch'])

    def test_v235_optin_does_not_activate_v216_even_with_token(self):
        with patch.dict(v216.os.environ,{
             'BOAT_EDGE_GITHUB_ACTIONS_TOKEN':'fixture',
             'BOAT_EDGE_EXTERNAL_V235_ENABLED':'true',
             'BOAT_EDGE_EXTERNAL_V216_ENABLED':'false'},clear=True), \
             patch.object(v216,'api_json') as api:
            self.assertEqual(v216.main(['--live']),0)
            api.assert_not_called()

    def test_v216_explicit_enable_still_needs_token(self):
        with patch.dict(v216.os.environ,{
             'BOAT_EDGE_EXTERNAL_V216_ENABLED':'true'},clear=True), \
             patch.object(v216,'api_json') as api:
            self.assertEqual(v216.main(['--live']),2)
            api.assert_not_called()

    def test_dry_run_is_read_only(self):
        recorded=[]
        def api(method,route,token,body=None):
            recorded.append((method,route,body))
            if route.startswith('/contents/'):
                return {'encoding':'base64','content':base64.b64encode(
                    json.dumps(CATALOG).encode()).decode()}
            if route.endswith('/runs?branch=main&per_page=100'):
                return runs()
            return WORKFLOW
        with patch.object(v216,'api_json',side_effect=api), \
             patch.object(v216,'utc_now',return_value=NOW):
            self.assertEqual(v216.main([]),0)
        self.assertEqual([m for m in recorded if m[0]=='POST'],[])

    def test_live_post_only_to_existing_v216_main(self):
        recorded=[]
        def api(method,route,token,body=None):
            recorded.append((method,route,body))
            if method=='POST':
                return {}
            if route.startswith('/contents/'):
                return {'encoding':'base64','content':base64.b64encode(
                    json.dumps(CATALOG).encode()).decode()}
            if route.endswith('/runs?branch=main&per_page=100'):
                return runs()
            return WORKFLOW
        with patch.dict(v216.os.environ,{
            'BOAT_EDGE_EXTERNAL_V216_ENABLED':'true',
            'BOAT_EDGE_GITHUB_ACTIONS_TOKEN':'fixture'},clear=True), \
            patch.object(v216,'api_json',side_effect=api), \
            patch.object(v216,'utc_now',return_value=NOW):
            self.assertEqual(v216.main(['--live']),0)
        self.assertEqual([m for m in recorded if m[0]=='POST'],[
            ('POST','/actions/workflows/BOAT_EDGE_V216_SOURCE_DIAGNOSTIC.yml/dispatches',
             {'ref':'main'})])

    def test_two_checks_independent_and_no_duplicate_paid_cron(self):
        with patch.object(combo.prediction,'main',return_value=1) as p, \
             patch.object(combo.observation,'main',return_value=0) as v:
            self.assertEqual(combo.main(['--live']),1)
            p.assert_called_once_with(['--live'])
            v.assert_called_once_with(['--live'])


if __name__=='__main__':
    unittest.main()
