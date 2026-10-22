import hashlib,tempfile,unittest
from pathlib import Path
from datetime import datetime,timezone,timedelta
from unittest.mock import MagicMock,patch
import scheduled_probe as sp
JST=timezone(timedelta(hours=9))
class DedupTests(unittest.TestCase):
 def test_identical_daily_bytes_share_inode(self):
  now=datetime(2026,10,23,10,0,tzinfo=JST)
  url="https://boatracecsv.github.io/data/programs/title/2026/10/23.csv"
  title=("レースコード,電話投票締切予定\n202610231201,10:45\n202610231202,10:50\n").encode()
  r=MagicMock();r.status=200;r.geturl.return_value=url;r.read.return_value=title
  r.__enter__.return_value=r
  daily=b"same day racecard source"
  digest=hashlib.sha256(daily).hexdigest()
  def fake_probe(code,deadline,source,root,opener=None):
   dest=Path(root)/code;dest.mkdir(parents=True,exist_ok=True)
   (dest/"body.body").write_bytes(daily)
   return {"sha256":digest,"body_name":"body.body"}
  with tempfile.TemporaryDirectory() as directory:
   with patch.object(sp,"run_probe",fake_probe):
    report=sp.run(now,root=directory,opener=lambda *a,**k:r)
   a=Path(directory)/"202610231201"/"body.body"
   b=Path(directory)/"202610231202"/"body.body"
   self.assertEqual(report["captured"],2)
   self.assertEqual(report["linked_duplicate_bodies"],1)
   self.assertEqual(a.stat().st_ino,b.stat().st_ino)
   self.assertEqual(a.read_bytes(),daily)
if __name__=="__main__":unittest.main()
