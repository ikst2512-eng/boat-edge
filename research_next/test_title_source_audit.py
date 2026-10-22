import hashlib,json,tempfile,unittest
from pathlib import Path
from probe_report import report

class TitleAuditTests(unittest.TestCase):
 def test_valid_source_does_not_count_as_race(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/"_source_title";p.mkdir()
   body="レースコード,電話投票締切予定\n202610231201,10:30\n".encode()
   (p/"schedule.body").write_bytes(body)
   (p/"schedule.json").write_text(json.dumps({
     "source_url":"https://boatracecsv.github.io/data/programs/title/2026/10/23.csv",
     "captured_jst":"2026-10-23T07:00:00+09:00",
     "sha256":hashlib.sha256(body).hexdigest(),"bytes":len(body),
     "source_publication_time_proven":False
   }))
   r=report(d)
   self.assertEqual(r["title_sources"],1)
   self.assertEqual(r["invalid_title_sources"],0)
   self.assertEqual(r["invalid"],0)
   self.assertEqual(r["eligible_12"],0)
 def test_corrupted_title_refused(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/"_source_title";p.mkdir()
   (p/"schedule.body").write_bytes(b"tampered")
   (p/"schedule.json").write_text(json.dumps({
    "source_url":"https://boatracecsv.github.io/data/programs/title/2026/10/23.csv",
    "captured_jst":"2026-10-23T07:00:00+09:00",
    "sha256":"0"*64,"bytes":8,"source_publication_time_proven":False
   }))
   r=report(d)
   self.assertEqual(r["invalid_title_sources"],1)
if __name__=="__main__":unittest.main()
