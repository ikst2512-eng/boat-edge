import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from site_mode_venue_v170 import calc, source_record, VENUES, MODES

class ResearchVenueTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
  self.h=self.root/'data/site_prediction_history';self.e=self.root/'data/site_learning/site_mode_evaluations_v136';self.h.mkdir(parents=True);self.e.mkdir(parents=True)
  self.key='20261009-02-08';self.win='1-3-5'
  self.hist={'race_key':self.key,'snapshot':{'race_key':self.key,'prediction_kind':'SITE_REFERENCE_V122','snapshot_window':'FINAL_15M','guards':{'results_seen':False,'unlock':False,'scoring':False},'saved_at':'2026-10-09T05:00:00+00:00','modes':{}},'settlement':{'settled_at':'2026-10-09T05:35:00+00:00','winning_combo':self.win,'payout':1350,'mode_hits':{}}}
  self.evaluation={'schema_version':'boat-edge-site-mode-evaluation-v136','scope':'SITE_REFERENCE_POST_SETTLEMENT_ONLY_NOT_FORMAL_FRESH','race_key':self.key,'snapshot_saved_at':'2026-10-09T05:00:00+00:00','winning_combo':self.win,'modes':{}}
  for k in MODES:
   t=[{'combo':self.win,'stake_yen':1000},{'combo':'1-2-3','stake_yen':9000}] if k!='hole' else [{'combo':'1-2-3','stake_yen':10000}]
   self.hist['snapshot']['modes'][k]={'tickets':t};self.hist['settlement']['mode_hits'][k]=(k!='hole');self.evaluation['modes'][k]={'hit':k!='hole','count':len(t),'ticket_rank':1 if k!='hole' else None}
  self.write()
 def tearDown(self):self.tmp.cleanup()
 def write(self):
  d=json.dumps(self.hist,ensure_ascii=False,indent=2)+'\n';b=d.encode('utf8');(self.h/(self.key+'.json')).write_bytes(b)
  self.evaluation['source_history_sha256']=hashlib.sha256(b).hexdigest();(self.e/(self.key+'.json')).write_text(json.dumps(self.evaluation,ensure_ascii=False),encoding='utf8')
 def test_genuine_snapshot_roi(self):
  r=source_record(self.e/(self.key+'.json'),self.h)
  self.assertTrue(r['modes']['hit']['hit']);self.assertEqual(13500,r['modes']['hit']['returned_yen']);self.assertEqual(0,r['modes']['hole']['returned_yen'])
 def test_entire_venue_table(self):
  o=calc(self.root);self.assertEqual(1,o['audited_races']);self.assertEqual(24,len(o['venues']));self.assertEqual('SMALL_SAMPLE',o['venues']['02']['status']);self.assertEqual(135.,o['venues']['02']['modes']['hit']['roi_pct']);self.assertEqual(0,o['venues']['01']['races']);self.assertEqual(0,o['excluded'])
 def test_hash_mismatch_rejected(self):
  p=self.h/(self.key+'.json');p.write_bytes(p.read_bytes()+b' ')
  with self.assertRaisesRegex(ValueError,'SHA mismatch'):source_record(self.e/(self.key+'.json'),self.h)
 def test_result_time_guard(self):
  self.hist['settlement']['settled_at']='2026-10-09T04:00:00+00:00';self.write()
  with self.assertRaisesRegex(ValueError,'prior to settlement'):source_record(self.e/(self.key+'.json'),self.h)
 def test_budget_required(self):
  self.hist['snapshot']['modes']['hit']['tickets'][0]['stake_yen']=900
  self.write()
  with self.assertRaisesRegex(ValueError,'not 10,000'):source_record(self.e/(self.key+'.json'),self.h)
 def test_formal_date_excluded_without_opening(self):
  (self.e/'20261008-02-08.json').write_text('THIS MUST NOT BE READ',encoding='utf8')
  r=calc(self.root);self.assertEqual(1,r['audited_races']);self.assertEqual(0,r['excluded'])

if __name__=='__main__':unittest.main()
