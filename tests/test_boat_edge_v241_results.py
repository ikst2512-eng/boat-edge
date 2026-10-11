import datetime as dt
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parent.parent/'scripts'))
import boat_edge_v241_results as m
from boat_edge_v241_patch_home import patch_text

REQUIRED='''<main id="homeView" class="view active">
<div class="brandtext">BOAT EDGE <small>v30</small></div>
<button class="primary-btn" id="refreshTopBtn">今すぐ更新</button>
<button data-view="auditView"><span class="navicon">✓</span>監査</button>
</head>
</body>'''

def write(p,obj):
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(obj,sort_keys=True,ensure_ascii=False)+'\n',encoding='utf-8')

class ResultsTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        subprocess.run(['git','init','-q'],cwd=self.root,check=True)
        subprocess.run(['git','config','user.name','test'],cwd=self.root,check=True)
        subprocess.run(['git','config','user.email','test@example.invalid'],cwd=self.root,check=True)
        self.key='20261011-19-06'
        self.deadline='2026-10-11T19:56:00+09:00'
        self.frozen=self.root/m.BASE/'v232_cohort'/(self.key+'.json')
        self.scored=self.root/m.BASE/'v234_scored'/(self.key+'.json')
        self.bet=['1-2-3','1-3-2','1-3-5','1-6-3','1-4-3','3-1-2','2-1-3','4-1-3','1-5-3','5-1-3']
        stakes=[1000]*10
        self.modes={k:[{'combo':combo,'stake_yen':stake} for combo,stake in zip(self.bet,stakes)] for k in m.MODES}
        self.c={'schema':m.V232,'scope':'SITE_REFERENCE_UNSEEN_PRE_RESULT_ONLY_NOT_FORMAL_FRESH',
                'race_key':self.key,'deadline_jst':self.deadline,'head_top1':'1','model_id':'SITE_REFERENCE_V122',
                'top3':self.bet[:3],'top5':self.bet[:5],'top10':self.bet,
                'formal_results_seen':False,'formal_gate_unlocked':False,'paper_purchases_authorized':False,'real_purchases_authorized':False,
                'frozen_mode_tickets':self.modes}
        write(self.root/'data/formal_status.json',{'guards':{'results_seen':False,'unlock':False,'scoring':False,'RESULT_UNLOCK_TOKEN':None},'formalFirst100':{'races':0}})
        write(self.frozen,self.c)
        self.commit('2026-10-11T10:48:00+00:00')
        sha=m.sha(self.frozen)
        self.first_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=self.root,text=True).strip()
        self.result={'schema':m.V234,'scope':'POST_RESULT_SITE_RESEARCH_ONLY_FORMAL_FRESH_LOCKED',
                     'race_key':self.key,'venue':'下関','deadline_jst':self.deadline,
                     'cohort_sha256':sha,'first_git_commit':self.first_commit,'first_git_committed_at':'2026-10-11T10:48:00+00:00',
                     'result_source':'https://www.boatrace.jp/owpc/pc/race/raceresult?hd=20261011&jcd=19&rno=6',
                     'result_fetched_at':'2026-10-11T11:08:00+00:00','model_id':'SITE_REFERENCE_V122',
                     'winning_combo':'1-3-5','official_payout_per_100_yen':720,'actual_head':'1','head_hit':True,
                     'top3_hit':True,'top5_hit':True,'top10_hit':True,'model_promotion_authorized':False,
                     'real_or_paper_wagers_placed':0,'modes':{name:{'hit':True,'frozen_stake_yen':10000,'tickets':10,'hypothetical_return_yen':7200} for name in m.MODES}}
        write(self.scored,self.result)
        self.commit('2026-10-11T11:15:00+00:00')

    def commit(self,at):
        subprocess.run(['git','add','-A'],cwd=self.root,check=True)
        env={**os.environ,'GIT_AUTHOR_DATE':at,'GIT_COMMITTER_DATE':at}
        subprocess.run(['git','commit','-qm','site audit fixture'],cwd=self.root,check=True,env=env)

    def test_one_verified_site_result(self):
        r=m.examine(self.root,self.scored)
        self.assertTrue(r['top10_hit'])
        self.assertEqual(r['official_payout_per_100_yen'],720)
        self.assertEqual(r['mode_outcomes']['hit']['hypothetical_return_yen'],7200)
        self.assertEqual(r['mode_outcomes']['hit']['hypothetical_profit_yen'],-2800)
        self.assertEqual(r['first_frozen_commit'],self.first_commit)

    def test_deterministic_aggregate(self):
        o=m.build(self.root)
        self.assertEqual(o['settled_verified_races'],1)
        self.assertEqual(o['top10_hits'],1)
        self.assertEqual(o['top10_hit_rate_percent'],100)
        self.assertFalse(o['formal_result_access'])
        self.assertEqual(json.dumps(o,sort_keys=True),json.dumps(m.build(self.root),sort_keys=True))

    def test_no_score_without_immutable_predeadline_record(self):
        self.c['top10']=['3-1-2']
        write(self.frozen,self.c)
        with self.assertRaisesRegex(ValueError,'COHORT|FIRST_CONTENT'):
            m.examine(self.root,self.scored)

    def test_no_score_if_official_result_url_wrong_race(self):
        self.result['result_source']=self.result['result_source'].replace('jcd=19','jcd=18')
        write(self.scored,self.result)
        with self.assertRaisesRegex(ValueError,'GIT_FIRST_CONTENT_CHANGED|RESULT_SOURCE_MISMATCH'):
            m.examine(self.root,self.scored)

    def test_no_fabricated_payout(self):
        self.result['official_payout_per_100_yen']=730
        write(self.scored,self.result)
        with self.assertRaisesRegex(ValueError,'GIT_FIRST_CONTENT_CHANGED|PARITY_FAILED'):
            m.examine(self.root,self.scored)

    def test_no_head_only_target_badge(self):
        self.result['winning_combo']='1-2-4'
        self.result['top3_hit']=False;self.result['top5_hit']=False;self.result['top10_hit']=False
        self.result['modes']={k:{'hit':False,'frozen_stake_yen':10000,'tickets':10,'hypothetical_return_yen':0} for k in m.MODES}
        write(self.scored,self.result)
        with self.assertRaisesRegex(ValueError,'GIT_FIRST_CONTENT_CHANGED'):
            m.examine(self.root,self.scored)
        # Even a head-correct miss is a non-hit under stored ticket membership.
        self.assertEqual('1-2-4'[0],self.c['head_top1'])
        self.assertNotIn('1-2-4',self.c['top10'])

    def test_formal_guard_must_remain_closed(self):
        x=read(self.root/'data/formal_status.json');x['guards']['unlock']=True
        write(self.root/'data/formal_status.json',x)
        with self.assertRaisesRegex(ValueError,'FORMAL_FRESH_GATE'):
            m.build(self.root)

    def test_wrong_model_id(self):
        self.c['model_id']='UNTRUSTED';write(self.frozen,self.c)
        with self.assertRaises(ValueError):m.examine(self.root,self.scored)

    def test_missing_frozen_mode(self):
        self.c['frozen_mode_tickets'].pop('hit');write(self.frozen,self.c)
        with self.assertRaises(ValueError):m.examine(self.root,self.scored)

    def test_all_boat_numbers_distinct(self):
        for c in ['1-1-2','7-3-2','1-2-2','']:
            self.assertFalse(m.valid_combo(c))
        self.assertTrue(m.valid_combo('1-2-3'))

    def test_pre_and_post_git_order(self):
        a,when=m.git_first(self.root,self.frozen)
        self.assertEqual(a,self.first_commit)
        self.assertLess(when,m.timestamp(self.deadline))
        b,after=m.git_first(self.root,self.scored)
        self.assertNotEqual(a,b)
        self.assertGreater(after,m.timestamp(self.deadline))

    def test_site_only_rows_empty_safe(self):
        (self.root/m.BASE/'v234_scored'/ (self.key+'.json')).unlink()
        o=m.build(self.root)
        self.assertEqual(o['settled_verified_races'],0)
        self.assertEqual(o['top10_hit_rate_percent'],None)

    def test_html_has_home_and_valid_result_hooks(self):
        page=(Path(__file__).parent.parent/'results.html').read_text(encoding='utf-8')
        for key in ['id="be241Mode"','id="be241Results"','href="./index.html"','id="be241Refresh"','data-filter="hit"','id="be241Wins"','id="be241Head"']:
            self.assertIn(key,page)
        self.assertNotIn('raceresult?',page)

    def test_patch_index_idempotence_and_restricted_scope(self):
        patched=patch_text(REQUIRED)
        self.assertIn('href="./results.html" class="be241-nav-link"',patched)
        self.assertIn('id="be241HomeResults"',patched)
        self.assertEqual(patch_text(patched),patched)
        self.assertEqual(patched.count('id="be241HomeResults"'),1)

    def test_partial_patch_drifts_closed(self):
        with self.assertRaisesRegex(ValueError,'PARTIAL_V241'):
            patch_text(REQUIRED+'\n<div id="be241HomeResults"></div>')

    def test_original_index_anchors_required(self):
        with self.assertRaisesRegex(ValueError,'ANCHOR'):
            patch_text(REQUIRED.replace('<button data-view="auditView">','<button data-view="other">'))


def read(path):return json.loads(path.read_text(encoding='utf-8'))

if __name__=='__main__':unittest.main()
