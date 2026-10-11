import datetime as dt
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent/'scripts'))
import boat_edge_v239_second_tail as m

KEY='20261012-09-10'
DEADLINE='2026-10-12T15:07:00+09:00'
PRE_TIME='2026-10-12T05:57:00+00:00'
FREEZE_TIME='2026-10-12T05:58:00+00:00'
SCORE_TIME='2026-10-12T06:19:00+00:00'


def write(path, value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,sort_keys=True)+'\n',encoding='utf-8')


class V239Tests(unittest.TestCase):
    def setUp(self):
        self.d=tempfile.TemporaryDirectory();self.addCleanup(self.d.cleanup)
        self.root=Path(self.d.name)
        write(self.root/'data/formal_status.json',{'guards':{'results_seen':False,'unlock':False,'scoring':False,'RESULT_UNLOCK_TOKEN':None},'formalFirst100':{'races':0}})
        self.cpath=self.root/m.PATH/'v232_cohort'/f'{KEY}.json'
        self.hit=['1-2-3','1-3-2','1-2-4','1-4-2','1-3-4','2-1-3','2-3-1','3-1-2','4-1-2','5-1-2']
        self.balance=['1-2-3','1-3-2','1-5-2','1-4-2','1-3-4','2-1-3','2-3-1','3-1-2','4-1-2','5-1-2']
        self.hole=['1-6-3','1-5-3','3-1-4','3-4-1','4-2-1','2-4-1','5-3-2','3-1-2','2-3-1','4-1-2']
        self.c={'schema':'BOAT_EDGE_V232_SITE_PROSPECTIVE_ACCURACY_COHORT_V1','scope':'SITE_REFERENCE_UNSEEN_PRE_RESULT_ONLY_NOT_FORMAL_FRESH',
         'race_key':KEY,'deadline_jst':DEADLINE,'snapshot_saved_at':'2026-10-12T05:56:50+00:00',
         'evidence_committed_at':PRE_TIME,'formal_results_seen':False,'formal_gate_unlocked':False,
         'paper_purchases_authorized':False,'real_purchases_authorized':False,'model_id':'SITE_REFERENCE_V122',
         'head_top1':'1','top10':self.hit,'frozen_mode_tickets':{
         'hit':[{'combo':x} for x in self.hit], 'balance':[{'combo':x} for x in self.balance],
         'hole':[{'combo':x} for x in self.hole]}}
        write(self.cpath,self.c)
        self.original_commit='a'*40
        self.challenger_commit='b'*40
        self.score_commit='c'*40
        self.now=m.stamp(FREEZE_TIME)
        self.official_path=self.root/m.PATH/'v234_scored'/f'{KEY}.json'
        self.frozen_path=self.root/m.PATH/'v239_frozen'/f'{KEY}.json'
        self.original_proof={'commit':self.original_commit,'at':m.stamp('2026-10-12T05:57:08+00:00'),'sha256':m.digest(self.cpath)}
        self.gitpatch=patch.object(m,'first_git',side_effect=self.git)
        self.gitpatch.start();self.addCleanup(self.gitpatch.stop)

    def git(self,root,path):
        if 'v232_cohort' in str(path):return dict(self.original_proof)
        if 'v239_frozen' in str(path):return {'commit':self.challenger_commit,'at':m.stamp('2026-10-12T05:58:09+00:00'),'sha256':m.digest(path)}
        if 'v234_scored' in str(path):return {'commit':self.score_commit,'at':m.stamp('2026-10-12T06:18:00+00:00'),'sha256':m.digest(path)}
        return None

    def official(self,win='1-6-3'):
        write(self.official_path,{'schema':'BOAT_EDGE_V234_PRECOMMITTED_SITE_ONLY_RESULT_SCORE_V1',
            'scope':'POST_RESULT_SITE_RESEARCH_ONLY_FORMAL_FRESH_LOCKED',
            'race_key':KEY,'cohort_sha256':m.digest(self.cpath),'winning_combo':win,
            'result_fetched_at':'2026-10-12T06:15:00+00:00',
            'result_source':'https://www.boatrace.jp/owpc/pc/race/raceresult?hd=20261012&jcd=09&rno=10',
            'top10_hit':win in self.hit})

    def test_exact_ten_and_predeclared_challengers(self):
        obj,error=m.prepare(self.root,self.cpath,self.now)
        self.assertIsNone(error)
        self.assertEqual(set(obj['comparators']),set(m.MODES))
        for tickets in obj['comparators'].values():
            self.assertEqual(len(tickets),10)
            self.assertEqual(len(set(tickets)),10)
        self.assertEqual(obj['comparators']['hit10'],self.hit)
        self.assertIn('1-5-2',obj['comparators']['second_diverse10'])
        self.assertIn('1-6-3',obj['comparators']['second_diverse10'])
        self.assertFalse(obj['result_seen_at_freeze'])

    def test_freeze_does_not_read_settlement(self):
        with patch.object(m,'read',wraps=m.read) as spy:
            x=m.freeze(self.root,self.now)
            self.assertEqual(x['frozen_today'],1)
            self.assertFalse(any('v234_scored' in str(v.args[0]) for v in spy.call_args_list))

    def test_no_retroactive_creation_after_deadline(self):
        r=m.freeze(self.root,m.stamp('2026-10-12T06:08:00+00:00'))
        self.assertEqual(r['new_frozen_this_run'],0)
        self.assertFalse(self.frozen_path.exists())

    def test_source_mutation_rejected(self):
        self.c['top10'][0]='1-6-3';write(self.cpath,self.c)
        _,error=m.prepare(self.root,self.cpath,self.now)
        self.assertEqual(error,'unverified_original_git_before_deadline')

    def test_formal_unlock_rejected(self):
        write(self.root/'data/formal_status.json',{'guards':{'results_seen':False,'unlock':True,'scoring':False,'RESULT_UNLOCK_TOKEN':None}})
        with self.assertRaisesRegex(RuntimeError,'FORMAL_GATE'):
            m.freeze(self.root,self.now)

    def test_freeze_idempotent(self):
        m.freeze(self.root,self.now)
        x=m.freeze(self.root,self.now+dt.timedelta(seconds=8))
        self.assertEqual(x['new_frozen_this_run'],0)

    def test_score_only_after_predeadline_git_and_verified_site_score(self):
        m.freeze(self.root,self.now)
        self.official()
        r=m.score(self.root,m.stamp(SCORE_TIME))
        self.assertEqual(r['scored_total'],1)
        self.assertEqual(r['comparisons']['hit10']['hits'],0)
        self.assertEqual(r['comparisons']['second_diverse10']['hits'],1)
        self.assertFalse(r['promotion_authorized'])
        self.assertEqual(m.score(self.root,m.stamp(SCORE_TIME))['new_scored_this_run'],0)

    def test_result_missing_does_not_score(self):
        m.freeze(self.root,self.now)
        r=m.score(self.root,m.stamp(SCORE_TIME))
        self.assertEqual(r['scored_total'],0)
        self.assertEqual(r['pending']['v234_site_verified_result_not_available'],1)

    def test_late_shadow_git_must_reject(self):
        m.freeze(self.root,self.now);self.official()
        old=self.git
        def late(root,path):
            if 'v239_frozen' in str(path):return {'commit':'z'*40,'at':m.stamp('2026-10-12T06:09:00+00:00'),'sha256':m.digest(path)}
            return old(root,path)
        with patch.object(m,'first_git',side_effect=late):
            obj,reason=m.score_one(self.root,self.frozen_path,m.stamp(SCORE_TIME))
        self.assertIsNone(obj)
        self.assertEqual(reason,'challenger_not_git_attested_before_deadline')

    def test_unverified_wrong_race_result_url_does_not_score(self):
        m.freeze(self.root,self.now);self.official()
        v=m.read(self.official_path);v['result_source']=v['result_source'].replace('jcd=09','jcd=08')
        write(self.official_path,v)
        obj,reason=m.score_one(self.root,self.frozen_path,m.stamp(SCORE_TIME))
        self.assertIsNone(obj)
        self.assertEqual(reason,'v234_result_url_invalid')

    def test_no_wrong_cohort_and_no_fabricated_rebalance(self):
        m.freeze(self.root,self.now);self.official()
        v=m.read(self.official_path);v['cohort_sha256']='f'*64
        write(self.official_path,v)
        _,reason=m.score_one(self.root,self.frozen_path,m.stamp(SCORE_TIME))
        self.assertEqual(reason,'v234_site_verified_result_not_available')

    def test_validation_of_combinations_and_clipped_unique(self):
        self.assertFalse(m.valid('1-1-2'))
        self.assertFalse(m.valid('1-2-7'))
        self.assertTrue(m.valid('1-2-3'))
        self.assertEqual(len(m.tail_swap(self.hit)),10)
        self.assertEqual(len(set(m.second_diverse(self.hit,self.balance,self.hole,'1'))),10)

    def test_formal_cohort_nonzero_rejected(self):
        write(self.root/'data/formal_status.json',{'guards':{'results_seen':False,'unlock':False,'scoring':False,'RESULT_UNLOCK_TOKEN':None},'formalFirst100':{'races':1}})
        with self.assertRaisesRegex(RuntimeError,'FORMAL_FIRST100'):
            m.freeze(self.root,self.now)

if __name__=='__main__':unittest.main()
