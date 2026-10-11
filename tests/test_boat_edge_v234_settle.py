import datetime as dt
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parent))
import boat_edge_v234_settle as M

KEY='20261011-16-10'
DUE='2026-10-11T15:37:00+09:00'
COMBOS=['1-2-5','1-5-2','1-2-4','1-4-2','1-5-4','2-1-5','5-1-2','3-1-2','3-2-1','4-1-2']
def iso(hm):return f'2026-10-11T{hm}+09:00'

def make_cohort():
    modes={}
    for name in ('hit','balance','hole','narrow'):
        modes[name]=[{'combo':c,'odds_at_freeze':15 if c in ('1-5-2','1-4-2') else 30,
                      'stake_yen':1000,'p_raw_percent':10} for c in COMBOS]
    return {'schema':M.FROZEN_SCHEMA,'scope':'SITE_REFERENCE_UNSEEN_PRE_RESULT_ONLY_NOT_FORMAL_FRESH',
            'race_key':KEY,'venue':'児島','deadline_jst':DUE,'snapshot_saved_at':iso('15:30:00'),
            'evidence_committed_at':iso('15:30:26'),'formal_results_seen':False,
            'formal_gate_unlocked':False,'model_id':'SITE_REFERENCE_V122',
            'real_purchases_authorized':False,'paper_purchases_authorized':False,
            'head_top1':'1','top3':COMBOS[:3],'top5':COMBOS[:5],'top10':COMBOS,
            'top10_10_to_20x_at_freeze':['1-5-2','1-4-2'],
            'frozen_mode_tickets':modes,'odds_combinations_verified':120}

def save(root,path,obj):
    p=root/path;p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(obj,sort_keys=True,ensure_ascii=False)+'\n')
    return p

class ScoringTest(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        subprocess.run(['git','init','-q','--initial-branch=main'],cwd=self.root,check=True)
        subprocess.run(['git','config','user.email','test@example.com'],cwd=self.root,check=True)
        subprocess.run(['git','config','user.name','Evidence Test'],cwd=self.root,check=True)
        self.now=M.time(iso('16:05:00'))
        save(self.root,'data/formal_status.json',{'guards':{'results_seen':False,'unlock':False,'scoring':False,'RESULT_UNLOCK_TOKEN':None},'formalFirst100':{'races':0}})
        self.path=save(self.root,f'data/site_autopilot/v232_cohort/{KEY}.json',make_cohort())
        self.result=save(self.root,f'data/site_results/{KEY}.json',{
            'schema_version':'boat-edge-site-result-v109','race_key':KEY,'status':'confirmed',
            'fetched_at':iso('15:54:49'),'source':'https://www.boatrace.jp/owpc/pc/race/raceresult?hd=20261011&jcd=16&rno=10',
            'finish_order':[5,1,2],'trifecta':'5-1-2','trifecta_payout_yen_per_100':7300})
        env=os.environ.copy();env.update(GIT_AUTHOR_DATE=iso('15:30:45'),GIT_COMMITTER_DATE=iso('15:30:45'))
        subprocess.run(['git','add','data/site_autopilot/v232_cohort/'+KEY+'.json'],cwd=self.root,check=True)
        subprocess.run(['git','commit','-q','-m','Predeadline immutable proof'],cwd=self.root,env=env,check=True)
    def test_valid_prospective_score(self):
        x,why=M.score(self.root,self.path,self.now)
        self.assertIsNone(why);self.assertEqual(x['winning_combo'],'5-1-2')
        self.assertFalse(x['head_hit']);self.assertFalse(x['top3_hit']);self.assertFalse(x['top5_hit'])
        self.assertTrue(x['top10_hit']);self.assertFalse(x['top10_10_20x_hit'])
        self.assertEqual(x['modes']['hit']['hypothetical_return_yen'],73000)
        self.assertFalse(x['model_promotion_authorized'])
    def test_score_committed_once_and_summary(self):
        a=M.run(self.root,self.now);b=M.run(self.root,self.now)
        self.assertEqual(a['settled_verified_races'],1);self.assertEqual(b['settled_verified_races'],1)
        self.assertEqual(a['top10_hit'],1);self.assertEqual(a['head_hit'],0)
        self.assertEqual(b['new_settled_races_this_run'],0)
        self.assertEqual(len(list((self.root/'data/site_autopilot/v234_scored').glob('*.json'))),1)
    def test_no_result_means_pending(self):
        self.result.unlink();x,why=M.score(self.root,self.path,self.now)
        self.assertIsNone(x);self.assertEqual(why,'confirmed_site_result_not_yet_available')
    def test_bad_result_source_fails_closed(self):
        j=M.read(self.result);j['source']=j['source'].replace('www.boatrace.jp','fake.example.com')
        save(self.root,f'data/site_results/{KEY}.json',j)
        self.assertEqual(M.score(self.root,self.path,self.now)[1],'result_origin_mismatch')
    def test_unconfirmed_does_not_score(self):
        j=M.read(self.result);j['status']='preliminary';save(self.root,f'data/site_results/{KEY}.json',j)
        self.assertEqual(M.score(self.root,self.path,self.now)[1],'unconfirmed_or_wrong_site_result')
    def test_wrong_finish_order_rejected(self):
        j=M.read(self.result);j['finish_order']=[1,5,2];save(self.root,f'data/site_results/{KEY}.json',j)
        self.assertEqual(M.score(self.root,self.path,self.now)[1],'result_contents_not_confirmable')
    def test_result_fetched_before_due_rejected(self):
        j=M.read(self.result);j['fetched_at']=iso('15:35:00');save(self.root,f'data/site_results/{KEY}.json',j)
        self.assertEqual(M.score(self.root,self.path,self.now)[1],'result_timing_invalid')
    def test_not_over_rejected(self):
        self.assertEqual(M.score(self.root,self.path,M.time(iso('15:38:00')))[1],'race_not_over')
    def test_post_commit_mutation_rejected(self):
        j=M.read(self.path);j['head_top1']='5';save(self.root,f'data/site_autopilot/v232_cohort/{KEY}.json',j)
        self.assertEqual(M.score(self.root,self.path,self.now)[1],'no_pre_deadline_git_commit_or_mutated_proof')
    def test_formal_guard_aborts_before_result_read(self):
        j=M.read(self.root/'data/formal_status.json');j['guards']['unlock']=True
        save(self.root,'data/formal_status.json',j)
        with self.assertRaisesRegex(RuntimeError,'V234_FORMAL_FRESH_GUARD_NOT_CLOSED'):M.run(self.root,self.now)
    def test_odds_band_must_match_frozen_tickets(self):
        j=M.read(self.path);j['top10_10_to_20x_at_freeze']=['1-2-5']
        save(self.root,f'data/site_autopilot/v232_cohort/{KEY}.json',j)
        self.assertEqual(M.score(self.root,self.path,self.now)[1],'no_pre_deadline_git_commit_or_mutated_proof')
    def test_scored_row_immutable(self):
        M.run(self.root,self.now)
        file=self.root/f'data/site_autopilot/v234_scored/{KEY}.json'
        file.write_text('NOT THE ORIGINAL')
        # Existing corrupted data must not be overwritten by a settlement rerun.
        with self.assertRaisesRegex(RuntimeError,'V234_CORRUPTED_SETTLED_PROOF'):
            M.summarize(self.root,self.now,0,{})

if __name__=='__main__':unittest.main()
