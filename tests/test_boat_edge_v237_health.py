import json
import tempfile
import unittest
from pathlib import Path
import datetime as dt
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import boat_edge_v237_health as m

class TestSiteHealth(unittest.TestCase):
    def setUp(self):
        self.t=tempfile.TemporaryDirectory();self.addCleanup(self.t.cleanup)
        self.root=Path(self.t.name)
        self.put('data/formal_status.json',{'guards':{'results_seen':False,'unlock':False,'scoring':False,'RESULT_UNLOCK_TOKEN':None},'formalFirst100':{'races':0}})
        self.put('data/site_autopilot/v232_current.json',{'schema':'BOAT_EDGE_V232_SITE_PROSPECTIVE_COHORT_SUMMARY_V1','day_jst':'20261011','frozen_research_races_today':19,'checked_at':'2026-10-11T13:01:00+00:00'})
        self.put('data/site_autopilot/v234_current.json',{'schema':'BOAT_EDGE_V234_SITE_ONLY_ACCURACY_SUMMARY_V1','settled_verified_races':15,'head_hit':8,'top3_hit':3,'top5_hit':4,'top10_hit':5,'checked_at':'2026-10-11T13:00:00+00:00'})
        self.put('data/site_autopilot/v236_pre_current.json',{'schema':'BOAT_EDGE_V236_HITRATE_PRE_RESULT_SUMMARY_V1','day_jst':'20261011','frozen_today':2})
        self.put('data/site_autopilot/v236_score_current.json',{'schema':'BOAT_EDGE_V236_HITRATE_SCORE_SUMMARY_V1','scored_total':2,'comparisons':{x:{'races':2,'hit':1,'avg_points':(15 if x=='coverage15' else 10)} for x in ('hit10','balance10','scenario7plus3','coverage15')},'status':'DESCRIPTIVE_FORWARD_SHADOW_NO_TUNING_NO_PROMOTION'})
        self.put('data/site_paper_sim/current.json',{'money':{'day':'20261011','daily_budget_yen':50000,'today_spent_yen':0,'today_paper_races':0,'virtual_only':True}})
        self.now=dt.datetime(2026,10,11,13,20,tzinfo=dt.timezone.utc)
    def put(self,path,data):
        p=self.root/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(data))
    def get(self,path):return m.read(self.root/path)
    def test_valid_metrics_and_label(self):
        r=m.build(self.root,self.now);self.assertEqual(r['current_reference']['settled_total'],15)
        self.assertEqual(r['current_reference']['registered_today'],19)
        self.assertEqual(r['research_candidates']['comparisons']['scenario7plus3']['hit_rate_percent'],50)
        self.assertFalse(r['accuracy_improvement_proven'])
    def test_date_rollover_does_not_relabel_yesterday(self):
        r=m.build(self.root,self.now+dt.timedelta(days=1));self.assertEqual(r['current_reference']['registered_today'],0)
        self.assertEqual(r['research_candidates']['pre_result_registered_today'],0)
        self.assertIsNone(r['simulator']['today_spent_yen'])
        self.assertIsNone(r['simulator']['today_remaining_yen'])
        self.assertFalse(r['simulator']['current_day_verified'])
    def test_idempotent_no_hourly_commit_noise(self):
        self.assertTrue(m.publish(self.root,self.now))
        before=(self.root/'data/site_autopilot/v237_current.json').read_bytes()
        self.assertFalse(m.publish(self.root,self.now+dt.timedelta(minutes=30)))
        self.assertEqual(before,(self.root/'data/site_autopilot/v237_current.json').read_bytes())
    def test_gate_result_seen_abort(self):
        s=self.get('data/formal_status.json');s['guards']['results_seen']=True;self.put('data/formal_status.json',s)
        with self.assertRaises(RuntimeError):m.build(self.root,self.now)
    def test_gate_token_abort(self):
        s=self.get('data/formal_status.json');s['guards']['RESULT_UNLOCK_TOKEN']='X';self.put('data/formal_status.json',s)
        with self.assertRaises(RuntimeError):m.build(self.root,self.now)
    def test_gate_fresh_active_abort(self):
        s=self.get('data/formal_status.json');s['formalFirst100']['races']=1;self.put('data/formal_status.json',s)
        with self.assertRaises(RuntimeError):m.build(self.root,self.now)
    def test_invalid_comparator_cannot_fake_hit(self):
        s=self.get('data/site_autopilot/v236_score_current.json');s['comparisons']['hit10']['hit']=3;self.put('data/site_autopilot/v236_score_current.json',s)
        with self.assertRaises(RuntimeError):m.build(self.root,self.now)
    def test_missing_report_fails_closed(self):
        (self.root/'data/site_autopilot/v236_score_current.json').unlink()
        with self.assertRaises(RuntimeError):m.build(self.root,self.now)
    def test_simulator_must_remain_virtual(self):
        s=self.get('data/site_paper_sim/current.json');s['money']['virtual_only']=False;self.put('data/site_paper_sim/current.json',s)
        with self.assertRaises(RuntimeError):m.build(self.root,self.now)
    def test_no_result_endpoint_referenced(self):
        code=Path(m.__file__).read_text()
        self.assertNotIn('data/site_results',code)
        self.assertNotIn('data/formal_prediction',code)
        self.assertNotIn('raceresult',code)

    def test_daily_50k_cap_and_remaining(self):
        s=self.get('data/site_paper_sim/current.json');s['money']['today_spent_yen']=10000
        self.put('data/site_paper_sim/current.json',s)
        self.assertEqual(m.build(self.root,self.now)['simulator']['today_remaining_yen'],40000)
        for field,value in [('today_spent_yen',50100),('daily_budget_yen',100000),('today_paper_races',-1)]:
            with self.subTest(field=field):
                bad={**s,'money':{**s['money'],field:value}};self.put('data/site_paper_sim/current.json',bad)
                with self.assertRaisesRegex(RuntimeError,'BUDGET'):m.build(self.root,self.now)

    def test_invalid_reference_counts_and_unequal_cohorts(self):
        s=self.get('data/site_autopilot/v234_current.json');s['top3_hit']=6
        self.put('data/site_autopilot/v234_current.json',s)
        with self.assertRaisesRegex(RuntimeError,'HIT_COUNTS'):m.build(self.root,self.now)
        s['top3_hit']=3;self.put('data/site_autopilot/v234_current.json',s)
        c=self.get('data/site_autopilot/v236_score_current.json');c['comparisons']['hit10']['races']=3
        self.put('data/site_autopilot/v236_score_current.json',c)
        with self.assertRaisesRegex(RuntimeError,'COMPARATOR'):m.build(self.root,self.now)

    def test_ten_point_comparison_cannot_report_fifteen_points(self):
        c=self.get('data/site_autopilot/v236_score_current.json');c['comparisons']['hit10']['avg_points']=15
        self.put('data/site_autopilot/v236_score_current.json',c)
        with self.assertRaisesRegex(RuntimeError,'POINT_BUDGET'):m.build(self.root,self.now)

if __name__=='__main__':unittest.main()
