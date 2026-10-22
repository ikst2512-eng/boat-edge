import json,unittest
from audit_frozen import verify
from feature_intake import ingest
class FrozenAuditTests(unittest.TestCase):
 def setUp(self):
  self.raw={"race_code":"202610231201","boats":[{"boat":i,"actual_entry":i,"exhibition_st":0.12} for i in range(1,7)]}
  self.original=json.dumps(self.raw).encode()
  self.record=ingest(self.raw,self.original,"2026-10-23T08:00:00+09:00","2026-10-23T18:00:00+09:00")
 def test_original_matches(self):
  result=verify(self.record,self.original)
  self.assertTrue(result["byte_consistent"])
  self.assertFalse(result["external_publication_proven"])
 def test_changed_byte(self):
  with self.assertRaises(ValueError):verify(self.record,self.original+b" ")
 def test_forged_feature(self):
  self.record["boats"][0]["actual_entry"]=6
  with self.assertRaises(ValueError):verify(self.record,self.original)
 def test_forged_capture_time(self):
  self.record["captured_at_jst"]="2026-10-23T18:00:00+09:00"
  with self.assertRaises(ValueError):verify(self.record,self.original)
 def test_unsupported_schema(self):
  self.record["schema"]="other"
  with self.assertRaises(ValueError):verify(self.record,self.original)
if __name__=="__main__":unittest.main()
