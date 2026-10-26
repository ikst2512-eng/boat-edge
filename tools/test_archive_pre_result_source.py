"""Unit tests for immutable official pre-deadline source capture."""
import datetime as dt
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from archive_pre_result_source import archive, JST

RACE={"race_key":"20261025-04-01","meta":{"date":"2026-10-25","venue_code":"04","race_no":1,"deadline":"10:52","phase":"PRE_RESULT","results_seen":False,"scoring":False,"unlock":False}}
BEFORE=dt.datetime(2026,10,25,10,40,tzinfo=JST)

class Response:
    status=200
    def __init__(self,url): self.url=url
    def __enter__(self): return self
    def __exit__(self,*_): return False
    def geturl(self): return self.url
    def read(self,n): return b"<html>pre-result fixture</html>"

class Opener:
    def open(self,request,timeout):
        return Response(request.full_url)

class ArchiveTests(unittest.TestCase):
    def test_capture_digest_and_reject_overwrite(self):
        with tempfile.TemporaryDirectory() as temp:
            manifest=archive(RACE,temp,now=BEFORE,opener=Opener())
            body=(Path(temp)/"20261025-04-01.beforeinfo.html").read_bytes()
            self.assertEqual(manifest["sha256"],hashlib.sha256(body).hexdigest())
            self.assertEqual(manifest["bytes"],len(body))
            self.assertEqual(json.loads((Path(temp)/"20261025-04-01.beforeinfo.audit.json").read_text())["sha256"],manifest["sha256"])
            with self.assertRaises(FileExistsError): archive(RACE,temp,now=BEFORE,opener=Opener())

    def test_reject_non_html_without_creating_evidence(self):
        class BadOpener:
            def open(self, request, timeout):
                class BadResponse(Response):
                    def read(self, n): return b'{"result":"not a prerace document"}'
                return BadResponse(request.full_url)
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaisesRegex(ValueError, "body_json_signature"):
                archive(RACE, temp, now=BEFORE, opener=BadOpener())
            self.assertEqual(list(Path(temp).iterdir()), [])

    def test_rejected_body_signatures_are_redacted(self):
        samples=[(b"\\x1f\\x8bcompressed", "body_gzip_signature"),
                 (b"<?xml version='1.0'?>", "body_xml_signature"),
                 (b"\\xef\\xbb\\xbf<html>bom</html>", "body_utf8_bom"),
                 (b"not-html-secret-content", "body_unknown_signature")]
        for payload,code in samples:
            class BadOpener:
                def open(self,request,timeout):
                    class BadResponse(Response):
                        def read(self,n): return payload
                    return BadResponse(request.full_url)
            with tempfile.TemporaryDirectory() as temp:
                with self.assertRaisesRegex(ValueError,"^"+code+"$"):
                    archive(RACE,temp,now=BEFORE,opener=BadOpener())
                self.assertEqual(list(Path(temp).iterdir()),[])

    def test_reject_after_deadline(self):
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaises(ValueError):
                archive(RACE,temp,now=BEFORE+dt.timedelta(minutes=15),opener=Opener())
            self.assertEqual(list(Path(temp).iterdir()),[])

    def test_reject_unlocked(self):
        race=dict(RACE,meta=dict(RACE["meta"],unlock=True))
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaises(ValueError): archive(race,temp,now=BEFORE,opener=Opener())

    def test_reject_identity_mismatch(self):
        race=dict(RACE,meta=dict(RACE["meta"],venue_code="05"))
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaises(ValueError): archive(race,temp,now=BEFORE,opener=Opener())

if __name__=="__main__":
    unittest.main()
