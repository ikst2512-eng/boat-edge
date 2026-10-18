from __future__ import annotations

from datetime import datetime, timedelta, timezone
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from boat_edge_01_v229_nearwindow_hold import plan, MAX_HOLD_SECONDS


class NearWindowHoldTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.now=datetime(2026,10,17,4,53,25,tzinfo=timezone.utc)
        self.jst=timezone(timedelta(hours=9))
        self.day=self.now.astimezone(self.jst).strftime('%Y%m%d')
        self.key=f'{self.day}-13-08'

    def put(self,path,value):
        p=self.root/path
        p.parent.mkdir(parents=True,exist_ok=True)
        p.write_text(json.dumps(value),encoding='utf-8')

    def ready(self,deadline_seconds=635,key=None):
        key=key or self.key
        due=self.now+timedelta(seconds=deadline_seconds)
        local=due.astimezone(self.jst)
        stamp=self.now.isoformat()
        self.put('data/today.json',{'date':local.strftime('%Y-%m-%d'),
            'venues':[{'races':[{'race_key':key,'deadline':local.strftime('%H:%M')}]}]})
        self.put(f'data/races/{key}.json',{'meta':{
            'phase':'PRE_RESULT','results_seen':False,'unlock':False,'scoring':False},
            'racers':[{}]*6,'source_audit':{
                'race_card':{'status':'ok','fetched_at':stamp},
                'beforeinfo':{'status':'ok','fetched_at':stamp}}})
        self.put(f'data/site_scratches_v182/{key}.json',{'race_key':key,
            'blocked':False,'checked_at':stamp,
            'race_card_source_status':'ok','official_beforeinfo_source_status':'ok'})
        combo={f'{a}-{b}-{c}':2.7 for a in range(1,7) for b in range(1,7)
               for c in range(1,7) if len({a,b,c})==3}
        self.put(f'data/site_odds/{key}.json',{'race_key':key,
            'phase':'PRE_RESULT_PURCHASE_ONLY','results_seen':False,
            'scoring':False,'available_count':120,
            'verified_official_dom_v167':True,'fetched_at':stamp,
            'trifecta_odds':combo})

    def test_wait_only_in_bounded_prewindow_after_live_inputs_are_ready(self):
        # Choose a minute-aligned deadline with 635 seconds remaining.
        self.ready(635)
        p=plan(self.root,self.now)
        self.assertEqual(p['race_key'],self.key)
        self.assertGreater(p['wait_seconds'],0)
        self.assertLessEqual(p['wait_seconds'],MAX_HOLD_SECONDS)
        self.assertEqual(p['reason'],'COARSE_SOURCE_READY_PREWINDOW_WAIT_ONLY')
        self.assertEqual(plan(self.root,self.now+timedelta(seconds=42))['wait_seconds'],0)

    def test_real_1834_gap_is_held_into_strict_window_without_backfill(self):
        """2026-10-18 Shimonoseki 3R: V229 ran 18:22:28, due 18:34.

        The previous 11m05 cap discarded this source-ready opportunity;
        Actions had no other V229 run before deadline. Holding is only a
        scheduling hint: a separate strict writer rechecks after the sleep.
        """
        self.now=datetime(2026,10,18,9,22,28,tzinfo=timezone.utc)
        self.day='20261018'
        self.key='20261018-19-03'
        self.ready(692)  # 11m32s before 18:34 JST
        result=plan(self.root,self.now)
        self.assertEqual(result['reason'],'COARSE_SOURCE_READY_PREWINDOW_WAIT_ONLY')
        self.assertEqual(result['race_key'],self.key)
        self.assertEqual(result['wait_seconds'],102)
        self.assertLessEqual(result['wait_seconds'],MAX_HOLD_SECONDS)
        # Once the wait elapses, there is no second hold and V229's own
        # source-, Git-, and pre-result gates remain sole freeze authority.
        later=self.now+timedelta(seconds=result['wait_seconds'])
        self.assertEqual((self.now+timedelta(seconds=692)-later).total_seconds(),590)
        self.assertEqual(plan(self.root,later)['wait_seconds'],0)

    def test_maximum_hold_is_bounded_and_earlier_races_do_not_block(self):
        # A minute-aligned 12m prewindow is the outer bound (130s hold).
        self.now=datetime(2026,10,17,4,53,0,tzinfo=timezone.utc)
        self.ready(720)
        result=plan(self.root,self.now)
        self.assertEqual(result['wait_seconds'],MAX_HOLD_SECONDS)
        self.assertEqual(MAX_HOLD_SECONDS,130)
        self.assertEqual(plan(self.root,self.now-timedelta(seconds=1))['wait_seconds'],0)
        # A late new source cannot become an eligible prediction merely
        # because a previous V229 process slept for the full allowance.
        blocked=self.root/f'data/site_odds/{self.key}.json'
        odds=json.loads(blocked.read_text())
        odds['available_count']=119
        self.put(f'data/site_odds/{self.key}.json',odds)
        self.assertEqual(plan(self.root,self.now)['wait_seconds'],0)

    def test_strict_current_window_never_waits_for_another_near_window_race(self):
        self.ready(635)
        key2=f'{self.day}-13-09'
        doc=json.loads((self.root/'data/today.json').read_text())
        due=(self.now+timedelta(seconds=295)).astimezone(self.jst)
        doc['venues'][0]['races'].append({'race_key':key2,'deadline':due.strftime('%H:%M')})
        self.put('data/today.json',doc)
        self.assertEqual(plan(self.root,self.now)['reason'],'UNSAVED_RACE_ALREADY_IN_STRICT_WINDOW')

    def test_incomplete_unofficial_or_blocked_inputs_never_hold(self):
        self.ready(635)
        odds=self.root/f'data/site_odds/{self.key}.json'
        doc=json.loads(odds.read_text())
        doc['available_count']=119
        self.put(f'data/site_odds/{self.key}.json',doc)
        self.assertEqual(plan(self.root,self.now)['wait_seconds'],0)
        doc['available_count']=120
        doc['verified_official_dom_v167']=False
        self.put(f'data/site_odds/{self.key}.json',doc)
        self.assertEqual(plan(self.root,self.now)['wait_seconds'],0)
        doc['verified_official_dom_v167']=True
        self.put(f'data/site_odds/{self.key}.json',doc)
        self.put(f'data/site_prediction_snapshots/{self.key}.json',{'already':'saved'})
        self.assertEqual(plan(self.root,self.now)['wait_seconds'],0)

    def test_invalid_day_duplicate_and_symlink_fail_closed(self):
        self.ready(635)
        target=self.root/'data/today.json'
        content=json.loads(target.read_text())
        content['venues'][0]['races'].append(content['venues'][0]['races'][0])
        self.put('data/today.json',content)
        self.assertEqual(plan(self.root,self.now)['wait_seconds'],0)
        content['venues'][0]['races']=content['venues'][0]['races'][:1]
        content['date']='2026-10-16'
        self.put('data/today.json',content)
        self.assertEqual(plan(self.root,self.now)['wait_seconds'],0)
        target.unlink()
        target.symlink_to(self.root/'data/races'/f'{self.key}.json')
        self.assertEqual(plan(self.root,self.now)['reason'],'CATALOG_PATH_UNSAFE')

    def test_workflow_preserves_same_writer_strict_guards_and_only_new_read_only_hold(self):
        wf=(ROOT/'.github/workflows/BOAT_EDGE_V229_ATOMIC_FREEZE_AUDIT.yml').read_text()
        self.assertIn('V229 optional bounded prewindow hold without relaxing 2-10m gate',wf)
        self.assertIn('python3 scripts/boat_edge_01_v229_nearwindow_hold.py',wf)
        self.assertIn('python3 scripts/boat_edge_v229_atomic_freeze.py',wf)
        self.assertIn('BOAT EDGE 3連単オッズ更新 V71',wf)
        self.assertIn("github.event.workflow_run.conclusion == 'success'",wf)
        self.assertIn("github.event.workflow_run.head_repository.full_name == github.repository",wf)
        self.assertEqual(wf.count('      - name: Commit only new snapshot, byte-matched official odds, and atomic SHA provenance'),1)


if __name__=='__main__':
    unittest.main()
