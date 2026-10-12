#!/usr/bin/env python3
"""V265: source-only regression. No results, payouts, combined APIs or formal unlock."""
import datetime as dt
import json
import pathlib
import sys
import tempfile
import unittest

sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
from boat_edge_v215_readiness import source_gaps

KEY='20261012-12-05'
NOW=dt.datetime.fromisoformat('2026-10-12T16:58:00+09:00')

def put(root,sub,obj):
    p=root/sub/(KEY+'.json')
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(obj),encoding='utf8')

class SourceIntegrity(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.root=pathlib.Path(self.tmp.name)
        self.race={'race_key':KEY,'racers':[{}]*6,'source_audit':{
            'race_card':{'status':'ok','fetched_at':'2026-10-12T16:55:00+09:00'},
            'beforeinfo':{'status':'ok','fetched_at':'2026-10-12T16:55:00+09:00'}}}
        self.scratch={'race_key':KEY,'blocked':False,'checked_at':'2026-10-12T16:55:00+09:00',
            'race_card_source_status':'ok','official_beforeinfo_source_status':'ok'}
        self.odds={'race_key':KEY,'phase':'PRE_RESULT_PURCHASE_ONLY','results_seen':False,'scoring':False,
            'fetched_at':'2026-10-12T16:55:00+09:00','verified_official_dom_v167':True,
            'available_count':120,'trifecta_odds':{f'{a}-{b}-{c}':12.3 for a in range(1,7)
                for b in range(1,7) for c in range(1,7) if len({a,b,c})==3}}
        self.write()
    def tearDown(self):self.tmp.cleanup()
    def write(self):
        put(self.root,'data/races',self.race)
        put(self.root,'data/site_scratches_v182',self.scratch)
        put(self.root,'data/site_odds',self.odds)
    def gaps(self):
        self.write()
        return source_gaps(self.root,KEY,NOW)
    def test_valid(self):self.assertEqual(self.gaps(),[])
    def test_beforeinfo_scratch_gate(self):
        self.scratch['official_beforeinfo_source_status']='published_wait'
        self.assertIn('scratch_stale',self.gaps())
    def test_60_quotes(self):
        self.odds['trifecta_odds']=dict(list(self.odds['trifecta_odds'].items())[:60])
        self.odds['available_count']=60
        self.assertIn('pre_result_odds_120_incomplete',self.gaps())
    def test_non_numeric(self):
        self.odds['trifecta_odds']['1-2-3']=None
        self.assertIn('pre_result_odds_120_incomplete',self.gaps())
    def test_zero(self):
        self.odds['trifecta_odds']['1-2-3']=0
        self.assertIn('pre_result_odds_120_incomplete',self.gaps())
    def test_fake_combo(self):
        self.odds['trifecta_odds']['1-1-2']=12.3
        self.assertIn('pre_result_odds_120_incomplete',self.gaps())
    def test_boolean(self):
        self.odds['trifecta_odds']['1-2-3']=True
        self.assertIn('pre_result_odds_120_incomplete',self.gaps())
    def test_no_dom_proof(self):
        self.odds.pop('verified_official_dom_v167')
        self.assertIn('official_dom_proof_missing',self.gaps())
    def test_scoring_true(self):
        self.odds['scoring']=True
        self.assertIn('pre_result_odds_unverified',self.gaps())
    def test_old_source(self):
        self.odds['fetched_at']='2026-10-12T16:30:00+09:00'
        self.assertIn('pre_result_odds_stale',self.gaps())

if __name__=='__main__':
    unittest.main()
