"""Offline publication gate: only proven predeadline first-add sidecars."""
import datetime as dt
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from prepare_public_entry_sidecars import prepare
from validate_pre_result_enrichment import JST

KEY="20261025-04-01"
NOW=dt.datetime(2026,10,25,10,45,tzinfo=JST)
RACE={"race_key":KEY,"meta":{"date":"2026-10-25","venue_code":"04","race_no":1,"deadline":"10:52","phase":"PRE_RESULT","results_seen":False,"unlock":False,"scoring":False},
      "racers":[{"lane":i,"registration_no":str(4000+i)} for i in range(1,7)]}
RAW=('<html><table><tr><th>コース</th><th>並び</th><th>ST</th></tr>'+''.join(f'<tr><td>{i}</td><td>{[2,1,3,4,5,6][i-1]}</td><td>.12</td></tr>' for i in range(1,7))+'</table></html>').encode()
AUDIT={"race_key":KEY,"kind":"official_beforeinfo_html","status":"ok",
       "source":"https://www.boatrace.jp/owpc/pc/race/beforeinfo?hd=20261025&jcd=04&rno=1",
       "fetched_at":"2026-10-25T10:40:00+09:00","sha256":hashlib.sha256(RAW).hexdigest(),"bytes":len(RAW)}

class PublicationTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.root=Path(self.temp.name)
        for folder in ("races","raw","enriched"):
            (self.root/folder).mkdir()
        (self.root/"races"/(KEY+".json")).write_text(json.dumps(RACE))
        (self.root/"raw"/(KEY+".beforeinfo.html")).write_bytes(RAW)
        (self.root/"raw"/(KEY+".beforeinfo.audit.json")).write_text(json.dumps(AUDIT))
        from ingest_verified_start_order import ingest
        (self.root/"enriched"/(KEY+".json")).write_text(json.dumps(ingest(RACE,RAW,AUDIT,now=NOW)))
    def tearDown(self):self.temp.cleanup()
    def run_prepare(self,when=NOW):
        return prepare(self.root/"races",self.root/"raw",self.root/"enriched",self.root/"published",now=when)
    def test_valid_published_create_only(self):
        result=self.run_prepare()
        self.assertEqual(result["prepared"],[KEY])
        sidecar=json.loads((self.root/"published"/(KEY+".json")).read_text())
        self.assertEqual(sidecar["actual_entry"],[2,1,3,4,5,6])
        self.assertEqual(self.run_prepare()["prepared"],[])
    def test_post_deadline_is_blocked(self):
        result=self.run_prepare(NOW+dt.timedelta(minutes=10))
        self.assertEqual(result["prepared"],[])
    def test_mutated_snapshot_blocked(self):
        item=self.root/"enriched"/(KEY+".json")
        altered=json.loads(item.read_text())
        altered["actual_entry"]=[1,2,3,4,5,6]
        item.write_text(json.dumps(altered))
        self.assertEqual(self.run_prepare()["prepared"],[])
    def test_tampered_html_blocked(self):
        (self.root/"raw"/(KEY+".beforeinfo.html")).write_bytes(RAW+b"tampered")
        self.assertEqual(self.run_prepare()["prepared"],[])

if __name__=="__main__":unittest.main()
