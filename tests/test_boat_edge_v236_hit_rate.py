import datetime as dt
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parent.parent/'scripts'))
import boat_edge_v236_hit_rate as m

KEY='20261012-09-10'
DUE='2026-10-12T15:07:00+09:00'
COHORT_TIME='2026-10-12T05:57:00+00:00'
FREEZE_TIME='2026-10-12T05:58:00+00:00'
RESULT_TIME='2026-10-12T06:15:00+00:00'

def write(p,d):
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(d,sort_keys=True)+'\n')

class Tests(unittest.TestCase):
    def setUp(self):
        self.d=tempfile.TemporaryDirectory();self.addCleanup(self.d.cleanup)
        self.root=Path(self.d.name)
        write(self.root/'data/formal_status.json',{'guards':{'results_seen':False,'unlock':False,'scoring':False,'RESULT_UNLOCK_TOKEN':None},'formalFirst100':{'races':0}})
        self.cp=self.root/m.PATH/'v232_cohort'/f'{KEY}.json'
        hit=['1-2-3','1-3-2','1-2-4','1-4-2','1-3-4','2-1-3','2-3-1','3-1-2','4-1-2','5-1-2']
        hole=['2-4-1','3-4-1','3-1-4','1-4-3','4-2-1','2-1-4','4-1-3','1-2-6','1-6-2','6-1-2','6-2-1','1-5-2']
        self.c={'schema':'BOAT_EDGE_V232_SITE_PROSPECTIVE_ACCURACY_COHORT_V1','race_key':KEY,
        'scope':'SITE_REFERENCE_UNSEEN_PRE_RESULT_ONLY_NOT_FORMAL_FRESH','model_id':'SITE_REFERENCE_V122',
        'deadline_jst':DUE,'evidence_committed_at':COHORT_TIME,'snapshot_saved_at':'2026-10-12T05:56:50+00:00',
        'formal_results_seen':False,'formal_gate_unlocked':False,'paper_purchases_authorized':False,'real_purchases_authorized':False,
        'top10':hit,'frozen_mode_tickets':{'hit':[{'combo':x} for x in hit],
        'balance':[{'combo':x} for x in hit], 'hole':[{'combo':x} for x in hole]}}
        write(self.cp,self.c)
        self.start=m.parse('2026-10-12T05:56:58+00:00')
        self.frozen=m.parse(FREEZE_TIME)
        self.original={'commit':'a'*40,'at':m.parse(COHORT_TIME),'sha256':m.sha(self.cp)}
        self.git_patch=patch.object(m,'git_first',side_effect=self.first)
        self.git_patch.start();self.addCleanup(self.git_patch.stop)
    def first(self,root,path):
        if 'v232_cohort' in str(path):return dict(self.original)
        if 'v236_frozen' in str(path):return {'commit':'b'*40,'at':m.parse('2026-10-12T05:58:25+00:00'),'sha256':m.sha(path)}
        return None
    def test_freeze_before_result_no_result_input(self):
        with patch.object(m,'load',wraps=m.load) as spy:
            x=m.freeze(self.root,self.frozen)
            self.assertEqual(x['frozen_today'],1)
            self.assertFalse(any('site_results' in str(c.args[0]) for c in spy.call_args_list))
        c=m.load(self.root/m.PATH/'v236_frozen'/f'{KEY}.json')
        self.assertEqual(c['comparators']['hit10'],self.c['top10'])
        self.assertEqual(len(c['comparators']['scenario7plus3']),10)
        self.assertEqual(len(c['comparators']['coverage15']),15)
        self.assertFalse(c['result_seen_at_freeze'])
    def test_freeze_idempotent(self):
        m.freeze(self.root,self.frozen)
        x=m.freeze(self.root,self.frozen+dt.timedelta(seconds=10))
        self.assertEqual(x['new_frozen_this_run'],0)
    def test_no_backfill_after_deadline(self):
        x=m.freeze(self.root,m.parse('2026-10-12T06:08:00+00:00'))
        self.assertEqual(x['frozen_today'],0)
    def test_formal_guard_blocks_freeze(self):
        write(self.root/'data/formal_status.json',{'guards':{'results_seen':True,'unlock':False,'scoring':False,'RESULT_UNLOCK_TOKEN':None}})
        with self.assertRaisesRegex(RuntimeError,'FORMAL_GATE'):
            m.freeze(self.root,self.frozen)
    def test_mutated_source_rejected(self):
        self.original['sha256']='f'*64
        s,err=m.prepare(self.root,self.cp,self.frozen)
        self.assertIsNone(s)
        self.assertEqual(err,'original_cohort_not_committed_unchanged_before_deadline')
    def test_duplicate_rejected(self):
        self.c['frozen_mode_tickets']['hit'][1]['combo']=self.c['frozen_mode_tickets']['hit'][0]['combo']
        write(self.cp,self.c);self.original['sha256']=m.sha(self.cp)
        s,err=m.prepare(self.root,self.cp,self.frozen)
        self.assertEqual(err,'ticket_sources_incomplete')
    def test_unconfirmed_result_does_not_score(self):
        m.freeze(self.root,self.frozen)
        p=self.root/'data/site_results'/f'{KEY}.json'
        write(p,{'race_key':KEY,'status':'pending'})
        x=m.score(self.root,m.parse(RESULT_TIME))
        self.assertEqual(x['scored_total'],0)
    def test_confirmed_result_scores_only_earlier_frozen(self):
        m.freeze(self.root,self.frozen)
        p=self.root/'data/site_results'/f'{KEY}.json'
        write(p,{'schema_version':'boat-edge-site-result-v109','race_key':KEY,'status':'confirmed','fetched_at':RESULT_TIME,
          'trifecta':'2-4-1','finish_order':[2,4,1], 'trifecta_payout_yen_per_100':3140,
          'source':'https://www.boatrace.jp/owpc/pc/race/raceresult?hd=20261012&jcd=09&rno=10'})
        x=m.score(self.root,m.parse(RESULT_TIME))
        self.assertEqual(x['scored_total'],1)
        self.assertEqual(x['comparisons']['hit10']['hit'],0)
        self.assertEqual(x['comparisons']['scenario7plus3']['hit'],1)
        self.assertFalse(x['promotion_authorized'])
        self.assertEqual(m.score(self.root,m.parse(RESULT_TIME))['new_scored_this_run'],0)
    def test_late_git_commit_must_reject(self):
        m.freeze(self.root,self.frozen)
        def mock(root,path):
            if 'v236_frozen' in str(path):return {'commit':'b'*40,'at':m.parse('2026-10-12T06:08:00+00:00'),'sha256':m.sha(path)}
            return dict(self.original)
        with patch.object(m,'git_first',side_effect=mock):
            s,reason=m.score_row(self.root,self.root/m.PATH/'v236_frozen'/f'{KEY}.json',m.parse(RESULT_TIME))
            self.assertIsNone(s)
            self.assertEqual(reason,'shadow_not_git_frozen_before_deadline')
    def test_git_timestamp_second_rounding_accepts_802ms_only(self):
        m.freeze(self.root,self.frozen)
        path=self.root/m.PATH/'v236_frozen'/f'{KEY}.json'
        row=m.load(path)
        row['frozen_at']='2026-10-12T05:58:00.802+00:00'
        write(path,row)
        def first_second(root,p):
            if 'v236_frozen' in str(p):
                return {'commit':'b'*40,'at':m.parse('2026-10-12T05:58:00+00:00'),'sha256':m.sha(p)}
            return dict(self.original)
        with patch.object(m,'git_first',side_effect=first_second):
            obj,reason=m.score_row(self.root,path,m.parse(RESULT_TIME))
        # Passes immutable source/timestamp/ticket gates, then waits for a
        # confirmed SITE result. No real hit is asserted by this fixture.
        self.assertIsNone(obj)
        self.assertEqual(reason,'site_official_result_unconfirmed')

    def test_git_timestamp_inversion_over_one_second_rejects_before_result(self):
        m.freeze(self.root,self.frozen)
        path=self.root/m.PATH/'v236_frozen'/f'{KEY}.json'
        row=m.load(path)
        row['frozen_at']='2026-10-12T05:58:00.802+00:00'
        write(path,row)
        def too_early(root,p):
            if 'v236_frozen' in str(p):
                return {'commit':'b'*40,'at':m.parse('2026-10-12T05:57:59+00:00'),'sha256':m.sha(p)}
            return dict(self.original)
        with patch.object(m,'git_first',side_effect=too_early), patch.object(m,'load',wraps=m.load) as spy:
            obj,reason=m.score_row(self.root,path,m.parse(RESULT_TIME))
            self.assertIsNone(obj)
            self.assertEqual(reason,'candidate_freeze_time_invalid')
            self.assertFalse(any('site_results' in str(call.args[0]) for call in spy.call_args_list))

    def test_source_wrong_venue_rejected(self):
        result={'schema_version':'boat-edge-site-result-v109','race_key':KEY,'status':'confirmed','fetched_at':RESULT_TIME,
            'trifecta':'2-4-1','finish_order':[2,4,1], 'trifecta_payout_yen_per_100':3140,
            'source':'https://www.boatrace.jp/owpc/pc/race/raceresult?hd=20261012&jcd=08&rno=10'}
        self.assertFalse(m.confirmed_result(result,KEY,m.parse(DUE)))
    def test_official_url_prefix_must_not_bypass_exact_race(self):
        result={'schema_version':'boat-edge-site-result-v109','race_key':KEY,'status':'confirmed','fetched_at':RESULT_TIME,
            'trifecta':'2-4-1','finish_order':[2,4,1], 'trifecta_payout_yen_per_100':3140,
            'source':'https://www.boatrace.jp/owpc/pc/race/raceresult?hd=20261012&jcd=091&rno=10'}
        self.assertFalse(m.confirmed_result(result,KEY,m.parse(DUE)))
    def test_result_not_before_deadline(self):
        result={'schema_version':'boat-edge-site-result-v109','race_key':KEY,'status':'confirmed','fetched_at':COHORT_TIME,
            'trifecta':'2-4-1','finish_order':[2,4,1], 'trifecta_payout_yen_per_100':3140,
            'source':'https://www.boatrace.jp/owpc/pc/race/raceresult?hd=20261012&jcd=09&rno=10'}
        self.assertFalse(m.confirmed_result(result,KEY,m.parse(DUE)))
    def test_tickets_unique_even_if_hole_duplicates(self):
        out=m.unique_extend(self.c['top10'],self.c['top10']+['2-4-1','3-4-1','3-1-4'],13)
        self.assertEqual(len(out),13)
        self.assertEqual(len(set(out)),13)

    def test_active_or_unknown_formal_cohort_blocks_before_any_outcome_read(self):
        for first in ({'races':1},{},{'races':False}):
            with self.subTest(first=first):
                status=m.load(self.root/'data/formal_status.json');status['formalFirst100']=first
                write(self.root/'data/formal_status.json',status)
                with patch.object(m,'load',wraps=m.load) as spy:
                    with self.assertRaisesRegex(RuntimeError,'COHORT'):m.score(self.root,m.parse(RESULT_TIME))
                    self.assertFalse(any('site_results' in str(c.args[0]) for c in spy.call_args_list))

    def test_candidate_tampering_is_rejected_before_result_read(self):
        m.freeze(self.root,self.frozen)
        path=self.root/m.PATH/'v236_frozen'/f'{KEY}.json'
        good=m.load(path)
        for field,value in [('scope','FORMAL'),('race_key','20261012-01-01'),
                            ('result_seen_at_freeze',True),('production_model_changed',True),
                            ('comparators',{**good['comparators'],'hit10':good['comparators']['coverage15']}),
                            ('frozen_at','2026-10-12T06:00:00+00:00')]:
            with self.subTest(field=field):
                write(path,{**good,field:value})
                with patch.object(m,'load',wraps=m.load) as spy:
                    obj,reason=m.score_row(self.root,path,m.parse(RESULT_TIME))
                    self.assertIsNone(obj)
                    self.assertFalse(any('site_results' in str(c.args[0]) for c in spy.call_args_list))

    def test_wrong_source_scope_key_and_day_rejected(self):
        for field,value in [('scope','FORMAL'),('race_key','20261012-01-01'),
                            ('deadline_jst','2026-10-13T15:07:00+09:00'),('model_id','UNPROVEN')]:
            with self.subTest(field=field):
                write(self.cp,{**self.c,field:value});self.original['sha256']=m.sha(self.cp)
                obj,reason=m.prepare(self.root,self.cp,self.frozen)
                self.assertIsNone(obj)

    def test_result_rejects_nonfinite_payout_future_time_and_wrong_schema(self):
        good={'schema_version':'boat-edge-site-result-v109','race_key':KEY,'status':'confirmed',
              'fetched_at':RESULT_TIME,'trifecta':'2-4-1','finish_order':[2,4,1],
              'trifecta_payout_yen_per_100':1500,
              'source':'https://www.boatrace.jp/owpc/pc/race/raceresult?hd=20261012&jcd=09&rno=10'}
        now=m.parse(RESULT_TIME)
        self.assertTrue(m.confirmed_result(good,KEY,m.parse(DUE),now))
        for field,value in [('trifecta_payout_yen_per_100',float('nan')),
                            ('trifecta_payout_yen_per_100',float('inf')),
                            ('fetched_at','2026-10-12T07:15:00+00:00'),('schema_version','FORMAL')]:
            with self.subTest(field=field):
                self.assertFalse(m.confirmed_result({**good,field:value},KEY,m.parse(DUE),now))

if __name__=='__main__':unittest.main()
