"""Synthetic HTTP-to-disk-to-audit integration checks; never request results."""
import tempfile, unittest
from unittest.mock import patch
from datetime import datetime, timedelta, timezone
from pathlib import Path
from scheduled_probe import run
from probe_availability import run_probe
from probe_report import report
from probe_health import assess

JST=timezone(timedelta(hours=9))
NOW=datetime(2026,10,23,10,0,tzinfo=JST)
CODE="202610231201"
BASE="https://boatracecsv.github.io/data/programs/"
TITLE=BASE+"title/2026/10/23.csv"
CARD=BASE+"race_cards/2026/10/23.csv"
class Response:
 status=200
 def __init__(self,url,body):self.url,self.body=url,body
 def read(self,n):return self.body[:n]
 def geturl(self):return self.url
 def __enter__(self):return self
 def __exit__(self,*args):return False
class IntegrationTests(unittest.TestCase):
 def collect(self,root):
  title=("レースコード,電話投票締切予定\n"+CODE+",11:00\n").encode()
  card=("レースコード,"+",".join(f"艇{i}_全国勝率" for i in range(1,7))+"\n"+CODE+",5.5,5.5,5.5,5.5,5.5,5.5\n").encode()
  def opener(request,timeout=12):
   url=request.full_url
   if url not in (TITLE,CARD):raise AssertionError("Unexpected source")
   return Response(url,title if url==TITLE else card)
  def capture(code,deadline,source,path,opener=None):
   return run_probe(code,deadline,source,path,clock=lambda:NOW,opener=opener)
  with patch("scheduled_probe.run_probe",side_effect=capture):
   totals=run(now=NOW,root=root,opener=opener,capture_clock=lambda:NOW)
  totals["status"]="ok"
  return totals
 def test_valid_synthetic_capture(self):
  with tempfile.TemporaryDirectory() as root:
   status=self.collect(root)
   summary=report(root)
   self.assertEqual((status["due"],status["captured"],status["failed"]),(1,1,0))
   self.assertEqual((summary["invalid"],summary["eligible_12"],summary["eligible_11"],summary["eligible_10"]),(0,1,1,1))
   health=assess(status,summary)
   self.assertEqual(health["state"],"PROBE_EVIDENCE_PRESENT_NOT_EXTERNALLY_ATTESTED")
 def test_two_races_share_one_daily_card_fetch(self):
  other="202610231202"
  title=("レースコード,電話投票締切予定\n"+CODE+",11:00\n"+other+",11:05\n").encode()
  header="レースコード,"+",".join("艇%d_全国勝率"%i for i in range(1,7))+"\n"
  card=(header+CODE+",5,5,5,5,5,5\n"+other+",5,5,5,5,5,5\n").encode()
  calls=[]
  def opener(req,timeout=12):
   calls.append(req.full_url)
   if req.full_url==TITLE:return Response(TITLE,title)
   if req.full_url==CARD:return Response(CARD,card)
   raise ValueError("unexpected URL")
  def capture(code,deadline,url,root,opener=None):
   return run_probe(code,deadline,url,root,clock=lambda:NOW,opener=opener)
  with tempfile.TemporaryDirectory() as root:
   with patch("scheduled_probe.run_probe",side_effect=capture):
    status=run(now=NOW,root=root,opener=opener,capture_clock=lambda:NOW)
   summary=report(root)
   self.assertEqual((status["due"],status["captured"],status["failed"]),(2,2,0))
   self.assertEqual(calls.count(CARD),1)
   self.assertEqual((summary["invalid"],summary["eligible_10"]),(0,2))
   self.assertEqual(assess({**status,"status":"ok"},summary)["state"],"PROBE_EVIDENCE_PRESENT_NOT_EXTERNALLY_ATTESTED")
 def test_tampered_bytes_rejected(self):
  with tempfile.TemporaryDirectory() as root:
   status=self.collect(root)
   body=next((Path(root)/CODE).glob("*.body"))
   body.write_bytes(body.read_bytes()+b"tampered")
   summary=report(root)
   self.assertEqual(summary["invalid"],1)
   self.assertEqual(assess(status,summary)["state"],"INVALID_CAPTURE_EVIDENCE")
if __name__=="__main__":unittest.main()
