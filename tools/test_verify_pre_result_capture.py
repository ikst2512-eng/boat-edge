"""Offline tests for read-only captured HTML evidence verification."""
import datetime as dt
import hashlib
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parent))
from verify_pre_result_capture import verify
RAW=b"<!doctype html><html><body>start exhibition</body></html>"
RACE={"race_key":"20261025-04-01","meta":{"date":"2026-10-25","venue_code":"04","race_no":1,"deadline":"10:52","phase":"PRE_RESULT","results_seen":False,"unlock":False,"scoring":False}}
AUDIT={"race_key":"20261025-04-01","status":"ok","kind":"official_beforeinfo_html","source":"https://www.boatrace.jp/owpc/pc/race/beforeinfo?hd=20261025&jcd=04&rno=1","fetched_at":"2026-10-25T10:40:00+09:00","sha256":hashlib.sha256(RAW).hexdigest(),"bytes":len(RAW)}

class VerifyCaptureTests(unittest.TestCase):
    def test_valid(self):
        self.assertTrue(verify(RAW,AUDIT,RACE)["ok"])
    def test_tampered_html(self):
        self.assertIn("sha256_mismatch",verify(RAW+b"!",AUDIT,RACE)["errors"])
    def test_wrong_race(self):
        self.assertFalse(verify(RAW,dict(AUDIT,race_key="20261025-05-01"),RACE)["ok"])
    def test_after_deadline(self):
        self.assertIn("capture_not_predeadline",verify(RAW,dict(AUDIT,fetched_at="2026-10-25T10:53:00+09:00"),RACE)["errors"])
    def test_wrong_source(self):
        self.assertIn("source_mismatch",verify(RAW,dict(AUDIT,source="https://evil.test/"),RACE)["errors"])
    def test_unsafe_phase(self):
        race=dict(RACE,meta=dict(RACE["meta"],unlock=True))
        self.assertIn("unsafe_phase",verify(RAW,AUDIT,race)["errors"])
    def test_not_html(self):
        bad=b"plain text"
        audit=dict(AUDIT,sha256=hashlib.sha256(bad).hexdigest(),bytes=len(bad))
        self.assertIn("not_html_document",verify(bad,audit,RACE)["errors"])

if __name__=="__main__":
    unittest.main()
