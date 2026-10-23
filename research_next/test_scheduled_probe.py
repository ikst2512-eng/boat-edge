import io,unittest,tempfile
from datetime import datetime,timedelta,timezone
from unittest.mock import MagicMock
from scheduled_probe import run
JST=timezone(timedelta(hours=9))
class RunnerTests(unittest.TestCase):
 def test_only_upcoming_races_selected(self):
  now=datetime(2026,10,23,10,0,tzinfo=JST)
  # 10:10 in range, 11:00 in range, 10:09 too late, 13:01 too early.
  body=("レースコード,電話投票締切予定\n"+
        "202610231201,10:10\n202610231202,11:00\n202610231203,10:09\n202610231204,13:01\n").encode()
  r=MagicMock();r.status=200;r.read.return_value=body
  r.geturl.return_value="https://boatracecsv.github.io/data/programs/title/2026/10/23.csv"
  r.__enter__=MagicMock(return_value=r);r.__exit__=MagicMock(return_value=False)
  calls=[]
  with tempfile.TemporaryDirectory() as root:
   result=run(now,root=root,opener=lambda *a,**k:r,probe=lambda code,*a:calls.append(code))
  self.assertEqual(result["due"],2)
  self.assertEqual(calls,["202610231201","202610231202"])
 def test_card_http_error_is_recorded(self):
  from urllib.error import HTTPError
  now=datetime(2026,10,23,10,0,tzinfo=JST)
  body=b"\xe3\x83\xac\xe3\x83\xbc\xe3\x82\xb9\xe3\x82\xb3\xe3\x83\xbc\xe3\x83\x89,\xe9\x9b\xbb\xe8\xa9\xb1\xe6\x8a\x95\xe7\xa5\xa8\xe7\xb7\xa0\xe5\x88\x87\xe4\xba\x88\xe5\xae\x9a\n202610231201,11:00\n"
  response=MagicMock()
  response.status=200
  response.read.return_value=body
  response.geturl.return_value="https://boatracecsv.github.io/data/programs/title/2026/10/23.csv"
  response.__enter__=MagicMock(return_value=response)
  response.__exit__=MagicMock(return_value=False)
  def failing_probe(*args):
   raise HTTPError("https://example.invalid/card",404,"Not Found",None,None)
  with tempfile.TemporaryDirectory() as root:
   status=run(now,root=root,opener=lambda *a,**kw:response,probe=failing_probe)
  self.assertEqual(status["captured"],0)
  self.assertEqual(status["failed"],1)
  self.assertEqual(status["failures"][0]["http_status"],404)
 def test_duplicate_title_race_code_fails_closed(self):
  now=datetime(2026,10,23,10,0,tzinfo=JST)
  body=("レースコード,電話投票締切予定\n"
        "202610231201,11:00\n"
        "202610231201,11:00\n").encode()
  r=MagicMock();r.status=200;r.read.return_value=body
  r.geturl.return_value="https://boatracecsv.github.io/data/programs/title/2026/10/23.csv"
  r.__enter__=MagicMock(return_value=r);r.__exit__=MagicMock(return_value=False)
  with tempfile.TemporaryDirectory() as root:
   with self.assertRaisesRegex(ValueError,"duplicate race code"):
    run(now,root=root,opener=lambda *a,**k:r,probe=lambda *a:None)
 def test_duplicate_code_with_invalid_deadline_fails_closed(self):
  now=datetime(2026,10,23,10,0,tzinfo=JST)
  body=("レースコード,電話投票締切予定\n"
        "202610231201,11:00\n"
        "202610231201,invalid\n").encode()
  r=MagicMock();r.status=200;r.read.return_value=body
  r.geturl.return_value="https://boatracecsv.github.io/data/programs/title/2026/10/23.csv"
  r.__enter__=MagicMock(return_value=r);r.__exit__=MagicMock(return_value=False)
  with tempfile.TemporaryDirectory() as root:
   with self.assertRaisesRegex(ValueError,"duplicate race code"):
    run(now,root=root,opener=lambda *a,**k:r,probe=lambda *a:None)
 def test_invalid_schedules_fail_closed(self):
  now=datetime(2026,10,23,10,0,tzinfo=JST)
  body="レースコード,電話投票締切予定\\nBAD,11:00\\n202610231201,invalid\\n".replace("\\n","\n").encode()
  r=MagicMock();r.status=200;r.read.return_value=body
  r.geturl.return_value="https://boatracecsv.github.io/data/programs/title/2026/10/23.csv"
  r.__enter__=MagicMock(return_value=r);r.__exit__=MagicMock(return_value=False)
  with tempfile.TemporaryDirectory() as root:
   with self.assertRaisesRegex(ValueError,"invalid deadline"):
    run(now,root=root,opener=lambda *a,**k:r)
 def test_malformed_deadline_does_not_disappear_among_valid_races(self):
  now=datetime(2026,10,23,10,0,tzinfo=JST)
  body=("レースコード,電話投票締切予定\n"
        "202610231201,11:00\n"
        "202610231202,broken\n").encode()
  r=MagicMock();r.status=200;r.read.return_value=body
  r.geturl.return_value="https://boatracecsv.github.io/data/programs/title/2026/10/23.csv"
  r.__enter__=MagicMock(return_value=r);r.__exit__=MagicMock(return_value=False)
  with tempfile.TemporaryDirectory() as root:
   with self.assertRaisesRegex(ValueError,"invalid deadline for race 202610231202"):
    run(now,root=root,opener=lambda *a,**k:r,probe=lambda *a:None)
 def test_bad_race_code_does_not_disappear(self):
  now=datetime(2026,10,23,10,0,tzinfo=JST)
  body=("レースコード,電話投票締切予定\n"
        "202610231201,11:00\n"
        "NOT_A_RACE,11:30\n").encode()
  r=MagicMock();r.status=200;r.read.return_value=body
  r.geturl.return_value="https://boatracecsv.github.io/data/programs/title/2026/10/23.csv"
  r.__enter__=MagicMock(return_value=r);r.__exit__=MagicMock(return_value=False)
  with tempfile.TemporaryDirectory() as root:
   with self.assertRaisesRegex(ValueError,"invalid race code"):
    run(now,root=root,opener=lambda *a,**k:r,probe=lambda *a:None)
 def test_empty_title_feed_fails_closed(self):
  now=datetime(2026,10,23,10,0,tzinfo=JST)
  r=MagicMock();r.status=200;r.read.return_value=b"\xe3\x83\xac\xe3\x83\xbc\xe3\x82\xb9\xe3\x82\xb3\xe3\x83\xbc\xe3\x83\x89,\xe9\x9b\xbb\xe8\xa9\xb1\xe6\x8a\x95\xe7\xa5\xa8\xe7\xb7\xa0\xe5\x88\x87\xe4\xba\x88\xe5\xae\x9a\n"
  r.geturl.return_value="https://boatracecsv.github.io/data/programs/title/2026/10/23.csv"
  r.__enter__=MagicMock(return_value=r);r.__exit__=MagicMock(return_value=False)
  with tempfile.TemporaryDirectory() as root:
   with self.assertRaisesRegex(ValueError,"no race rows"):
    run(now,root=root,opener=lambda *a,**k:r)
if __name__=="__main__":unittest.main()
