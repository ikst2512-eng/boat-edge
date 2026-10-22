import json,tempfile,unittest
from pathlib import Path
from readiness import summarize
class ReadinessTests(unittest.TestCase):
 def test_complete_and_incomplete(self):
  with tempfile.TemporaryDirectory() as d:
   paths=[]
   for i in (1,2):
    p=Path(d)/f"{i}.json"
    boats=[{"boat":n,"actual_entry":n,**({"exhibition_st":0.1,"lap_time":37,"turn_time":6,"straight_time":7} if i==1 else {})} for n in range(1,7)]
    p.write_text(json.dumps({"race_code":f"20261023120{i}","source_sha256":"a"*64,"captured_at_jst":"2026-10-23T08:00:00+09:00","deadline_jst":"2026-10-23T18:00:00+09:00","boats":boats,"exhibition_complete":i==1}))
    paths.append(p)
   s=summarize(paths)
   self.assertEqual(s["races"],2);self.assertEqual(s["exhibition_complete"],1);self.assertEqual(s["exhibition_missing"],1)
 def test_duplicate_rejected(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/"x.json"
   p.write_text(json.dumps({"race_code":"202610231201","source_sha256":"a"*64,"captured_at_jst":"2026-10-23T08:00:00+09:00","deadline_jst":"2026-10-23T18:00:00+09:00","boats":[{"actual_entry":n} for n in range(1,7)]}))
   with self.assertRaises(ValueError):summarize([p,p])
if __name__=="__main__":unittest.main()
