import hashlib,json,tempfile,unittest
from pathlib import Path
from probe_report import report
class ProbeReportTests(unittest.TestCase):
 def add_title(self,d):
  q=Path(d)/"_source_title";q.mkdir()
  data="レースコード,電話投票締切予定\n202610231201,18:00\n".encode()
  (q/"source.body").write_bytes(data)
  (q/"source.json").write_text(json.dumps({
   "source_url":"https://boatracecsv.github.io/data/programs/title/2026/10/23.csv",
   "captured_jst":"2026-10-23T17:40:00+09:00",
   "sha256":hashlib.sha256(data).hexdigest(),"bytes":len(data),
   "source_publication_time_proven":False}))

 def test_invalid_title_row_rejected_instead_of_skipped(self):
  with tempfile.TemporaryDirectory() as d:
   self.add_title(d)
   q=Path(d)/"_source_title"
   body=("レースコード,電話投票締切予定\\n"
         "202610231201,18:00\\n"
         "BAD,19:00\\n").replace("\\n","\n").encode()
   (q/"source.body").write_bytes(body)
   meta=json.loads((q/"source.json").read_text())
   meta["bytes"]=len(body)
   meta["sha256"]=hashlib.sha256(body).hexdigest()
   (q/"source.json").write_text(json.dumps(meta))
   observed=report(d)
   self.assertEqual(observed["invalid_title_sources"],1)
   self.assertEqual(observed["title_sources"],0)
 def test_duplicate_title_row_rejected(self):
  with tempfile.TemporaryDirectory() as d:
   self.add_title(d)
   q=Path(d)/"_source_title"
   body=("レースコード,電話投票締切予定\\n"
         "202610231201,18:00\\n"
         "202610231201,18:00\\n").replace("\\n","\n").encode()
   (q/"source.body").write_bytes(body)
   meta=json.loads((q/"source.json").read_text())
   meta["bytes"]=len(body)
   meta["sha256"]=hashlib.sha256(body).hexdigest()
   (q/"source.json").write_text(json.dumps(meta))
   observed=report(d)
   self.assertEqual(observed["invalid_title_sources"],1)
   self.assertEqual(observed["title_sources"],0)
 def test_reject_forged_cutoff(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/"202610231201";p.mkdir();self.add_title(d)
   body=("レースコード,"+",".join(f"艇{i}_全国勝率" for i in range(1,7))+"\n202610231201,6,6,6,6,6,6\n").encode();sha=hashlib.sha256(body).hexdigest()
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
   p=Path(d)/"202610231201";p.mkdir();self.add_title(d)
   body=("レースコード,"+",".join(f"艇{i}_全国勝率" for i in range(1,7))+"\n202610231201,6,6,6,6,6,6\n").encode();sha=hashlib.sha256(body).hexdigest()
   (p/"capture.body").write_bytes(body)
   m={"body_name":"capture.body","bytes":len(body),"sha256":sha,"target_race_validated":True,"race_code":"202610231201",
      "source_url":"https://boatracecsv.github.io/data/programs/race_cards/2026/10/23.csv",
      "deadline_jst":"2026-10-23T18:00:00+09:00","started_jst":"2026-10-23T17:45:00+09:00",
      "completed_jst":"2026-10-23T17:45:02+09:00","eligible_margins":[12,11,10]}
   (p/"capture.json").write_text(json.dumps(m))
   self.assertEqual(report(d)["eligible_12"],1)
 def test_wrong_race_in_archived_csv_rejected(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/"202610231201";p.mkdir();self.add_title(d)
   body=("レースコード,"+",".join(f"艇{i}_全国勝率" for i in range(1,7))+"\n202610231202,6,6,6,6,6,6\n").encode()
   (p/"capture.body").write_bytes(body)
   meta={"body_name":"capture.body","bytes":len(body),"sha256":hashlib.sha256(body).hexdigest(),"target_race_validated":True,
      "race_code":"202610231201","source_url":"https://boatracecsv.github.io/data/programs/race_cards/2026/10/23.csv",
      "deadline_jst":"2026-10-23T18:00:00+09:00","started_jst":"2026-10-23T17:45:00+09:00",
      "completed_jst":"2026-10-23T17:45:02+09:00","eligible_margins":[12,11,10]}
   (p/"capture.json").write_text(json.dumps(meta))
   self.assertEqual(report(d)["invalid"],1)
 def test_late_title_is_not_valid_evidence(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/"202610231201";p.mkdir();self.add_title(d)
   title_meta=Path(d)/"_source_title"/"source.json"
   t=json.loads(title_meta.read_text())
   t["captured_jst"]="2026-10-23T17:46:00+09:00"
   title_meta.write_text(json.dumps(t))
   body=("レースコード,"+",".join(f"艇{i}_全国勝率" for i in range(1,7))+"\\n202610231201,6,6,6,6,6,6\\n").encode()
   (p/"capture.body").write_bytes(body)
   m={"body_name":"capture.body","bytes":len(body),"sha256":hashlib.sha256(body).hexdigest(),
      "target_race_validated":True,"race_code":"202610231201",
      "source_url":"https://boatracecsv.github.io/data/programs/race_cards/2026/10/23.csv",
      "deadline_jst":"2026-10-23T18:00:00+09:00","started_jst":"2026-10-23T17:45:00+09:00",
      "completed_jst":"2026-10-23T17:45:02+09:00","eligible_margins":[12,11,10]}
   (p/"capture.json").write_text(json.dumps(m))
   self.assertEqual(report(d)["invalid"],1)
if __name__=="__main__":unittest.main()
