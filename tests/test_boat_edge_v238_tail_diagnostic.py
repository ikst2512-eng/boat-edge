import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parent.parent/'scripts'))
import boat_edge_v238_tail_diagnostic as m

KEY='20261011-01-06'
HIT=['1-2-3','1-3-2','1-2-4','1-4-2','1-3-4','2-1-3','2-3-1','3-1-2','4-1-2','5-1-2']
BAL=['1-2-3','1-3-2','1-2-4','1-4-2','1-3-4','2-1-3','2-3-1','3-1-2','4-1-2','6-1-2']

def write(p,d):
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(d),encoding='utf-8')

class TailTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        write(self.root/'data/formal_status.json',{'guards':{'results_seen':False,'unlock':False,'scoring':False,'RESULT_UNLOCK_TOKEN':None},'formalFirst100':{'races':0}})
        self.cp=self.root/'data/site_autopilot/v232_cohort'/f'{KEY}.json'
        self.sp=self.root/'data/site_autopilot/v234_scored'/f'{KEY}.json'
        self.c={'schema':'BOAT_EDGE_V232_SITE_PROSPECTIVE_ACCURACY_COHORT_V1','scope':'SITE_REFERENCE_UNSEEN_PRE_RESULT_ONLY_NOT_FORMAL_FRESH','race_key':KEY,
           'formal_results_seen':False,'formal_gate_unlocked':False,'paper_purchases_authorized':False,'real_purchases_authorized':False,
           'deadline_jst':'2026-10-11T17:48:00+09:00','head_top1':'1','top10':list(HIT),
           'frozen_mode_tickets':{'hit':[{'combo':v} for v in HIT],'balance':[{'combo':v} for v in BAL]}}
        write(self.cp,self.c)
        self.winning='1-2-3';self.update()
    def update(self):
        self.s={'schema':'BOAT_EDGE_V234_PRECOMMITTED_SITE_ONLY_RESULT_SCORE_V1','scope':'POST_RESULT_SITE_RESEARCH_ONLY_FORMAL_FRESH_LOCKED','race_key':KEY,
            'cohort_sha256':m.hash_file(self.cp),'first_git_commit':'a'*40,'first_git_committed_at':'2026-10-11T08:41:12+00:00',
            'result_fetched_at':'2026-10-11T08:58:00+00:00','winning_combo':self.winning,'head_prediction':'1',
            'head_hit':self.winning[0]=='1','top10_hit':self.winning in HIT,
            'model_promotion_authorized':False,'accuracy_improvement_proven':False,'venue':'桐生',
            'modes':{'hit':{'hit':self.winning in HIT},'balance':{'hit':self.winning in BAL}}}
        write(self.sp,self.s)
    def test_exact(self):
        self.assertEqual(m.verify_pair(self.root,self.sp,False)['reason'],'EXACT_TOP10_HIT')
    def test_swapped(self):
        self.winning='1-4-3';self.update()
        self.assertEqual(m.verify_pair(self.root,self.sp,False)['reason'],'SECOND_THIRD_SWAPPED')
    def test_head_miss(self):
        self.winning='6-5-4';self.update()
        self.assertEqual(m.verify_pair(self.root,self.sp,False)['reason'],'HEAD_MISS')
    def test_third_absent(self):
        self.winning='1-2-6';self.update()
        self.assertEqual(m.verify_pair(self.root,self.sp,False)['reason'],'THIRD_ABSENT')
    def test_both_absent(self):
        self.winning='1-5-6';self.update()
        self.assertEqual(m.verify_pair(self.root,self.sp,False)['reason'],'SECOND_AND_THIRD_ABSENT')
    def test_summary_and_unchanged(self):
        summary=m.build(self.root,False)
        self.assertEqual(summary['settled_verified_pairs'],1)
        self.assertEqual(summary['head_hits'],1)
        self.assertEqual(summary['paired_existing_10pt_modes_descriptive']['both_hit'],1)
        self.assertTrue(m.publish(self.root,False));self.assertFalse(m.publish(self.root,False))
    def test_head_miss_but_top10_hit_kept_separate(self):
        self.winning='2-1-3';self.update()
        report=m.build(self.root,False)
        self.assertEqual(report['head_hits'],0)
        self.assertEqual(report['head_miss_but_top10_hit'],1)
        self.assertEqual(report['head_hit_top10_miss'],0)
        self.assertEqual(report['paired_existing_10pt_modes_descriptive']['hit10_hits'],1)
    def test_closed_guard(self):
        write(self.root/'data/formal_status.json',{'guards':{'results_seen':False,'unlock':True,'scoring':False,'RESULT_UNLOCK_TOKEN':None},'formalFirst100':{'races':0}})
        with self.assertRaisesRegex(RuntimeError,'FORMAL_LOCK'):
            m.build(self.root,False)
    def test_provenance_tamper(self):
        self.c['top10'][0]='5-3-2';write(self.cp,self.c)
        with self.assertRaisesRegex(RuntimeError,'COHORT_BYTES_MISMATCH'):
            m.build(self.root,False)
    def test_no_git_proof_fails_closed(self):
        with patch.object(m,'first_commit',return_value=None):
            with self.assertRaisesRegex(RuntimeError,'FIRST_GIT_PROOF_INVALID'):
                m.build(self.root,True)
    def test_result_outcome_parity(self):
        self.s['top10_hit']=False;write(self.sp,self.s)
        with self.assertRaisesRegex(RuntimeError,'HEAD_TAIL_PARITY_INVALID'):
            m.build(self.root,False)
    def test_empty(self):
        self.sp.unlink()
        self.assertEqual(m.build(self.root,False)['settled_verified_pairs'],0)

if __name__=='__main__':unittest.main()
