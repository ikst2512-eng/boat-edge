import datetime as dt
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parent.parent/'scripts'))
import boat_edge_v240_coverage as m

KEY='20261012-09-10'
DUE='2026-10-12T15:07:00+09:00'
PRE='2026-10-12T05:57:00+00:00'
FREEZE='2026-10-12T05:58:00+00:00'
AFTER='2026-10-12T06:20:00+00:00'


def write(path,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(data,sort_keys=True)+'\n',encoding='utf-8')


class Tests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        write(self.root/'data/formal_status.json',{'guards':{'results_seen':False,'unlock':False,'scoring':False,'RESULT_UNLOCK_TOKEN':None},'formalFirst100':{'races':0}})
        self.cpath=self.root/m.PATH/'v232_cohort'/f'{KEY}.json'
        # Baseline supports second=2,3,4; missing second=5,6.
        self.hit=['1-2-3','1-3-2','1-2-4','1-4-2','1-3-4','2-1-3','2-3-1','3-1-2','4-1-2','5-1-2']
        self.balance=['1-2-3','1-3-2','1-2-4','1-4-2','1-3-4','1-5-3','3-1-5','2-3-1','4-1-2','5-1-2']
        self.hole=['5-1-3','3-1-5','2-1-5','1-4-5','1-3-6','3-2-1','6-1-2','2-4-1','4-2-1','1-2-5']
        self.c={'schema':'BOAT_EDGE_V232_SITE_PROSPECTIVE_ACCURACY_COHORT_V1','scope':'SITE_REFERENCE_UNSEEN_PRE_RESULT_ONLY_NOT_FORMAL_FRESH',
                'race_key':KEY,'deadline_jst':DUE,'snapshot_saved_at':'2026-10-12T05:56:50+00:00','evidence_committed_at':PRE,
                'formal_results_seen':False,'formal_gate_unlocked':False,'paper_purchases_authorized':False,'real_purchases_authorized':False,
                'model_id':'SITE_REFERENCE_V122','head_top1':'1','top10':self.hit,
                'frozen_mode_tickets':{'hit':[{'combo':x} for x in self.hit],'balance':[{'combo':x} for x in self.balance],
                                       'hole':[{'combo':x} for x in self.hole]}}
        write(self.cpath,self.c)
        self.output=self.root/m.PATH/'v240_frozen'/f'{KEY}.json'
        self.official=self.root/m.PATH/'v234_scored'/f'{KEY}.json'
        self.mock=patch.object(m,'first_git',side_effect=self.first)
        self.mock.start();self.addCleanup(self.mock.stop)

    def first(self,root,p):
        if 'v232_cohort' in str(p):return {'commit':'a'*40,'at':m.stamp('2026-10-12T05:57:05+00:00'),'sha256':m.sha(p)}
        if 'v240_frozen' in str(p):return {'commit':'b'*40,'at':m.stamp('2026-10-12T05:58:09+00:00'),'sha256':m.sha(p)}
        if 'v234_scored' in str(p):return {'commit':'c'*40,'at':m.stamp('2026-10-12T06:18:00+00:00'),'sha256':m.sha(p)}
        return None

    def result(self,winning='1-5-3'):
        write(self.official,{'schema':'BOAT_EDGE_V234_PRECOMMITTED_SITE_ONLY_RESULT_SCORE_V1',
                'scope':'POST_RESULT_SITE_RESEARCH_ONLY_FORMAL_FRESH_LOCKED','race_key':KEY,
                'cohort_sha256':m.sha(self.cpath),'winning_combo':winning,'top10_hit':winning in self.hit,
                'result_fetched_at':'2026-10-12T06:15:00+00:00',
                'result_source':'https://www.boatrace.jp/owpc/pc/race/raceresult?hd=20261012&jcd=09&rno=10'})

    def test_repair_26_of_27_identity_problem(self):
        b=m.second_coverage(self.hit,self.balance,self.hole)
        self.assertEqual(len(b),10)
        self.assertEqual(len(set(b)),10)
        self.assertEqual(b[:7],self.hit[:7])
        self.assertGreater(len(set(b)-set(self.hit)),0)
        self.assertTrue(any(x.startswith('1-5-') or x.startswith('1-6-') for x in b))

    def test_two_candidates_distinct_and_same_budget(self):
        o,error=m.prepare(self.root,self.cpath,m.stamp(FREEZE))
        self.assertIsNone(error)
        self.assertEqual(set(o['comparators']),set(m.MODES))
        self.assertEqual(o['comparators']['hit10'],self.hit)
        for picks in o['comparators'].values():
            self.assertEqual(len(picks),10)
            self.assertEqual(len(set(picks)),10)
        self.assertGreater(o['ticket_novelty_vs_hit10']['second_coverage10'],0)
        self.assertFalse(o['results_seen_at_freeze'])

    def test_freeze_never_reads_results(self):
        with patch.object(m,'read',wraps=m.read) as spy:
            result=m.freeze(self.root,m.stamp(FREEZE))
            self.assertEqual(result['frozen_today'],1)
            self.assertFalse(any('v234_scored' in str(c.args[0]) for c in spy.call_args_list))

    def test_late_creation_forbidden(self):
        m.freeze(self.root,m.stamp('2026-10-12T06:07:00+00:00'))
        self.assertFalse(self.output.exists())

    def test_parent_digest_attested(self):
        with patch.object(m,'first_git',return_value={'commit':'x'*40,'at':m.stamp(PRE),'sha256':'0'*64}):
            _,reason=m.prepare(self.root,self.cpath,m.stamp(FREEZE))
        self.assertEqual(reason,'unverified_parent_predeadline_commit')

    def test_block_formal_unlock(self):
        write(self.root/'data/formal_status.json',{'guards':{'results_seen':False,'unlock':True,'scoring':False,'RESULT_UNLOCK_TOKEN':None},'formalFirst100':{'races':0}})
        with self.assertRaisesRegex(RuntimeError,'FORMAL_FRESH'):m.freeze(self.root,m.stamp(FREEZE))

    def test_block_formal_first100(self):
        write(self.root/'data/formal_status.json',{'guards':{'results_seen':False,'unlock':False,'scoring':False,'RESULT_UNLOCK_TOKEN':None},'formalFirst100':{'races':1}})
        with self.assertRaisesRegex(RuntimeError,'FORMAL_FRESH'):m.freeze(self.root,m.stamp(FREEZE))

    def test_idempotence(self):
        m.freeze(self.root,m.stamp(FREEZE))
        summary=m.freeze(self.root,m.stamp('2026-10-12T05:58:15+00:00'))
        self.assertEqual(summary['new_frozen_this_run'],0)

    def test_score_future_verified_site_only(self):
        m.freeze(self.root,m.stamp(FREEZE));self.result()
        result=m.score(self.root,m.stamp(AFTER))
        self.assertEqual(result['scored_total'],1)
        self.assertEqual(result['comparisons']['hit10']['hits'],0)
        self.assertEqual(result['comparisons']['second_coverage10']['hits'],1)
        self.assertFalse(result['promotion_authorized'])
        self.assertEqual(m.score(self.root,m.stamp(AFTER))['new_scored_this_run'],0)

    def test_score_requires_result(self):
        m.freeze(self.root,m.stamp(FREEZE))
        o=m.score(self.root,m.stamp(AFTER))
        self.assertEqual(o['scored_total'],0)
        self.assertEqual(o['pending']['site_only_v234_result_unavailable'],1)

    def test_predeadline_gitrepo_proof_required(self):
        m.freeze(self.root,m.stamp(FREEZE));self.result()
        old=self.first
        def late(root,p):
            if 'v240_frozen' in str(p):return {'commit':'f'*40,'at':m.stamp('2026-10-12T06:09:00+00:00'),'sha256':m.sha(p)}
            return old(root,p)
        with patch.object(m,'first_git',side_effect=late):
            v,why=m.score_one(self.root,self.output,m.stamp(AFTER))
        self.assertIsNone(v)
        self.assertEqual(why,'candidate_not_git_frozen_before_deadline')

    def test_wrong_venue_result_rejected(self):
        m.freeze(self.root,m.stamp(FREEZE));self.result()
        old=m.read(self.official)
        old['result_source']=old['result_source'].replace('jcd=09','jcd=08');write(self.official,old)
        _,why=m.score_one(self.root,self.output,m.stamp(AFTER))
        self.assertEqual(why,'official_source_mismatch')

    def test_wrong_cohort_digest_rejected(self):
        m.freeze(self.root,m.stamp(FREEZE));self.result()
        old=m.read(self.official);old['cohort_sha256']='f'*64;write(self.official,old)
        _,why=m.score_one(self.root,self.output,m.stamp(AFTER))
        self.assertEqual(why,'site_only_v234_result_unavailable')

    def test_valid_permutations(self):
        for bad in ('1-1-2','1-2-7','1-2-3-4','1-2-2'):
            self.assertFalse(m.combo_valid(bad))
        self.assertTrue(m.combo_valid('1-2-3'))

if __name__=='__main__':unittest.main()
