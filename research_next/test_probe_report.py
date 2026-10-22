import hashlib,json,tempfile,unittest
from pathlib import Path
from probe_report import report
class ProbeReportTests(unittest.TestCase):
 def test_reject_forged_cutoff(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/"202610231201";p.mkdir()
   body=b"example captured content";sha=hashlib.sha256(body).hexdigest()
   (p/"capture.body").write_bytes(body)
   meta={"body_name":"capture.body","bytes":len(body),"sha256":sha,"target_race_validated":True,"race_code":"202610231201",
         "source_url":"https://boatracecsv.github.io/data/programs/race_cards/2026/10/23.csv",
         "deadline_jst":"2026-10-23T18:00:00+09:00","started_jst":"2026-10-23T17:49:00+09:00",
         "completed_jst":"2026-10-23T17:49:01+09:00","eligible_margins":[12,11,10]}
   (p/"capture.json").write_text(json.dumps(meta))
   result=report(d)
   self.assertEqual(result["invalid"],1)
   self.assertEqual(result["eligible_12"],0)
 def test_matching_cutoff(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/"202610231201";p.mkdir()
   body=b"captured bytes";sha=hashlib.sha256(body).hexdigest()
   (p/"capture.body").write_bytes(body)
   m={"body_name":"capture.body","bytes":len(body),"sha256":sha,"target_race_validated":True,"race_code":"202610231201",
      "source_url":"https://boatracecsv.github.io/data/programs/race_cards/2026/10/23.csv",
      "deadline_jst":"2026-10-23T18:00:00+09:00","started_jst":"2026-10-23T17:45:00+09:00",
      "completed_jst":"2026-10-23T17:45:02+09:00","eligible_margins":[12,11,10]}
   (p/"capture.json").write_text(json.dumps(m))
   self.assertEqual(report(d)["eligible_12"],1)
if __name__=="__main__":unittest.main()
