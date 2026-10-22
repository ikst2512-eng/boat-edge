import io,unittest
from datetime import datetime,timedelta,timezone
from unittest.mock import Mock
from scheduled_probe import run
JST=timezone(timedelta(hours=9))
class RunnerTests(unittest.TestCase):
 def test_only_upcoming_races_selected(self):
  now=datetime(2026,10,23,10,0,tzinfo=JST)
  # 10:10 in range, 11:00 in range, 10:09 too late, 11:01 too early.
  body=("レースコード,電話投票締切予定\n"+
        "202610231201,10:10\n202610231202,11:00\n202610231203,10:09\n202610231204,11:01\n").encode()
  r=Mock();r.status=200;r.read.return_value=body
  r.geturl.return_value="https://boatracecsv.github.io/data/programs/title/2026/10/23.csv"
  r.__enter__=Mock(return_value=r);r.__exit__=Mock(return_value=False)
  calls=[]
  result=run(now,opener=lambda *a,**k:r,probe=lambda code,*a:calls.append(code))
  self.assertEqual(result["due"],2)
  self.assertEqual(calls,["202610231201","202610231202"])
 def test_no_results_needed(self):
  now=datetime(2026,10,23,10,0,tzinfo=JST)
  r=Mock();r.status=200;r.read.return_value=b"\xe3\x83\xac\xe3\x83\xbc\xe3\x82\xb9\xe3\x82\xb3\xe3\x83\xbc\xe3\x83\x89,\xe9\x9b\xbb\xe8\xa9\xb1\xe6\x8a\x95\xe7\xa5\xa8\xe7\xb7\xa0\xe5\x88\x87\xe4\xba\x88\xe5\xae\x9a\n"
  r.geturl.return_value="https://boatracecsv.github.io/data/programs/title/2026/10/23.csv"
  r.__enter__=Mock(return_value=r);r.__exit__=Mock(return_value=False)
  result=run(now,opener=lambda *a,**k:r)
  self.assertEqual(result["due"],0)
if __name__=="__main__":unittest.main()
