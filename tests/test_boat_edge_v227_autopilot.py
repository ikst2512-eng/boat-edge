#!/usr/bin/env python3
"""Offline deterministic V227 regression tests. No network, no result read."""
import datetime as dt
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

SRC=Path(__file__).resolve().parents[1]/'scripts/boat_edge_v227_autopilot.py'
spec=importlib.util.spec_from_file_location('v227_autopilot',SRC)
app=importlib.util.module_from_spec(spec)
spec.loader.exec_module(app)
NOW=dt.datetime(2026,10,11,4,51,tzinfo=dt.timezone.utc)
KEY='20261011-09-08'

def save(root,name,doc):
    p=root/name;p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(doc,ensure_ascii=False,sort_keys=True),encoding='utf-8')
    return p


def race():
    return {'meta':{'phase':'PRE_RESULT','results_seen':False,'unlock':False,'scoring':False},
         'racers':[{'number':x} for x in range(1,7)],
         'source_audit':{'race_card':{'status':'ok','fetched_at':'2026-10-11T13:48:00+09:00'},
            'beforeinfo':{'status':'ok','fetched_at':'2026-10-11T13:48:00+09:00'}}}


def scratch():
    return {'race_key':KEY,'source_date':'20261011','blocked':False,
        'race_card_source_status':'ok','official_beforeinfo_source_status':'ok',
        'checked_at':'2026-10-11T13:49:00+09:00'}


def odds():
    return {'race_key':KEY,'phase':'PRE_RESULT_PURCHASE_ONLY',
      'fetched_at':'2026-10-11T13:49:00+09:00','trifecta_odds':dict.fromkeys(app.COMBOS,12.5)}


class TestAutopilot(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        save(self.root,'data/today.json',{'date':'2026-10-11','venues':[{'venue':'津',
            'races':[{'race_key':KEY,'deadline':'14:00'},
                     {'race_key':'20261010-09-07','deadline':'14:00'}]}]})
        save(self.root,'data/site_paper_sim/readiness_v215_current.json',{'day_jst':'20261011','day_observed_races':5,'day_verified_races':0,'day_latest_reasons':{'snapshot_missing':5}})
        save(self.root,'data/site_ops_v220/current.json',{'status':'NEEDS_ATTENTION','issues':['predeadline_incomplete']})
        save(self.root,'data/site_paper_sim/current.json',{'mode':'PAPER_ONLY','money':{'daily_budget_yen':50000,'today_spent_yen':0,'balance_yen':50000,'today_paper_races':0}})
        save(self.root,'data/formal_status.json',{'guards':{'results_seen':False,'unlock':False,'scoring':False,'RESULT_UNLOCK_TOKEN':None}})
        save(self.root,'data/site_autovalidation/current.json',{'performance_claim':'NOT_PROVEN','site_v185':{'verified_races':42},'site_v199':{'verified_races':24}})
        save(self.root,'data/races/'+KEY+'.json',race())
        save(self.root,'data/site_scratches_v182/'+KEY+'.json',scratch())
        save(self.root,'data/site_odds/'+KEY+'.json',odds())
        p=self.root/'scripts/site_final_history_v133.py';p.parent.mkdir(exist_ok=True)
        p.write_text('# V226_IMMUTABLE_ORIGINAL_SNAPSHOT\n# V226_SOURCE_GUARD\n# V226_DECISION_WINDOW\n# V226_ODDS_GUARD\n')

    def test_missing_prediction_fails_closed(self):
        report=app.summary(self.root,NOW)
        self.assertEqual(report['site']['readiness_observed_races'],5)
        self.assertEqual(report['site']['readiness_shadow_verified_races'],0)
        self.assertEqual(len(report['site']['current_window']),1)
        self.assertEqual(report['site']['current_window'][0]['issues'],['締切前予想未保存'])
        self.assertTrue(report['formal']['guard_closed'])
        self.assertEqual(report['paper']['spent_yen'],0)
        self.assertFalse(report['prediction']['production_improvement_proven'])
        self.assertTrue(report['site']['v226_source_guard_active'])

    def test_snapshot_sha_mismatch_never_passes(self):
        snap=save(self.root,'data/site_prediction_snapshots/'+KEY+'.json',{'race_key':KEY,'snapshot_window':'FINAL_15M','odds_sha256':'a'*64})
        save(self.root,'data/site_prediction_audit/'+KEY+'.json',{'pass':True,'latest_snapshot_sha256':'b'*64})
        self.assertIn('予想SHA監査未一致',app.risk(self.root,KEY,NOW))
        save(self.root,'data/site_prediction_audit/'+KEY+'.json',{'pass':True,'latest_snapshot_sha256':hashlib.sha256(snap.read_bytes()).hexdigest()})
        self.assertEqual(app.risk(self.root,KEY,NOW),[])

    def test_stale_and_incomplete_odds_and_scratch(self):
        o=odds();o['trifecta_odds'].pop('1-2-3')
        save(self.root,'data/site_odds/'+KEY+'.json',o)
        sc=scratch();sc['blocked']=True
        save(self.root,'data/site_scratches_v182/'+KEY+'.json',sc)
        issues=app.risk(self.root,KEY,NOW)
        self.assertIn('欠場照合未確認',issues)
        self.assertIn('最新オッズ120通り未確認',issues)
        self.assertIn('締切前予想未保存',issues)

    def test_no_results_read_and_idempotent_status(self):
        forbidden=self.root/'data/results'/f'{KEY}.json'
        forbidden.parent.mkdir(parents=True,exist_ok=True)
        forbidden.write_text('DO NOT READ',encoding='utf8')
        orig=Path.read_text
        def restricted(path,*args,**kwargs):
            if 'results' in path.parts or 'payout' in path.parts:
                raise AssertionError('FORBIDDEN_RESULT_READ')
            return orig(path,*args,**kwargs)
        with patch.object(Path,'read_text',restricted):
            d,first=app.run(self.root,NOW)
            _,second=app.run(self.root,NOW)
        self.assertTrue(first)
        self.assertFalse(second)
        self.assertFalse(d['formal']['results_read_by_v227'])
        self.assertTrue((self.root/'data/site_autopilot/v227_current.json').is_file())

    def test_future_or_stale_source_not_green(self):
        r=race();r['source_audit']['beforeinfo']['fetched_at']='2026-10-11T14:01:00+09:00'
        save(self.root,'data/races/'+KEY+'.json',r)
        self.assertIn('直前情報未取得または期限切れ',app.risk(self.root,KEY,NOW))
        sc=scratch();sc['checked_at']='2026-10-11T13:20:00+09:00'
        save(self.root,'data/site_scratches_v182/'+KEY+'.json',sc)
        self.assertIn('欠場照合未確認',app.risk(self.root,KEY,NOW))

if __name__=='__main__': unittest.main()
