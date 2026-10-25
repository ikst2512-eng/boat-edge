"""Check final published sidecar cutoff remains before race deadline."""
import datetime as dt
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from verify_sidecars_before_push import verify_staged, JST
KEY="20261025-04-01"
BEFORE=dt.datetime(2026,10,25,10,45,tzinfo=JST)
class FinalGateTests(unittest.TestCase):
 def setUp(self):
  self.t=tempfile.TemporaryDirectory()
  self.root=Path(self.t.name)
  (self.root/"data/races").mkdir(parents=True)
  (self.root/"data/site_verified_entries").mkdir(parents=True)
  self.name="data/site_verified_entries/"+KEY+".json"
  race={"race_key":KEY,"meta":{"date":"2026-10-25","deadline":"10:52","phase":"PRE_RESULT","results_seen":False,"unlock":False,"scoring":False}}
  (self.root/"data/races"/(KEY+".json")).write_text(json.dumps(race))
  side={"race_key":KEY,"actual_entry":[2,1,3,4,5,6],"source_audit":{"actual_entry":{"fetched_at":"2026-10-25T10:40:00+09:00"}}}
  (self.root/self.name).write_text(json.dumps(side))
 def tearDown(self):self.t.cleanup()
 def run_gate(self,now):
  with patch("verify_sidecars_before_push.Path",side_effect=lambda p:self.root/str(p)):
   return verify_staged([self.name],now=now)
 def test_before_deadline(self):self.assertTrue(self.run_gate(BEFORE))
 def test_after_deadline(self):
  with self.assertRaisesRegex(ValueError,"deadline_expired"):
   self.run_gate(BEFORE+dt.timedelta(minutes=8))
 def test_no_changes(self):
  with self.assertRaises(ValueError):verify_staged([],now=BEFORE)
 def test_unrelated_staged(self):
  with self.assertRaisesRegex(ValueError,"unexpected_staged_path"):
   verify_staged(["data/races/"+KEY+".json"],now=BEFORE)
 def test_at_exact_deadline(self):
  with self.assertRaisesRegex(ValueError,"deadline_expired"):
   self.run_gate(dt.datetime(2026,10,25,10,52,tzinfo=JST))
 def test_capture_at_deadline_rejected(self):
  side_path=self.root/self.name
  side=json.loads(side_path.read_text())
  side["source_audit"]["actual_entry"]["fetched_at"]="2026-10-25T10:52:00+09:00"
  side_path.write_text(json.dumps(side))
  with self.assertRaisesRegex(ValueError,"invalid_capture_time"):
   self.run_gate(BEFORE)
 def test_capture_without_timezone_rejected(self):
  side_path=self.root/self.name
  side=json.loads(side_path.read_text())
  side["source_audit"]["actual_entry"]["fetched_at"]="2026-10-25T10:40:00"
  side_path.write_text(json.dumps(side))
  with self.assertRaisesRegex(ValueError,"invalid_capture_time"):
   self.run_gate(BEFORE)
 def test_result_seen_rejected(self):
  race_path=self.root/"data/races"/(KEY+".json")
  race=json.loads(race_path.read_text())
  race["meta"]["results_seen"]=True
  race_path.write_text(json.dumps(race))
  with self.assertRaisesRegex(ValueError,"unsafe_race_phase"):
   self.run_gate(BEFORE)
if __name__=="__main__":unittest.main()
