import importlib.util, io, json, tempfile, unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

HERE=Path(__file__).resolve().parents[1]/'scripts'/'deadline_v9'/'capture.py'
spec=importlib.util.spec_from_file_location('capture_v9',HERE)
mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)

class FakeResponse:
    status=200
    headers={'Content-Type':'text/html; charset=utf-8'}
    def __init__(self,url,raw=b'<html>test</html>'):
        self.url=url; self.raw=raw
    def __enter__(self):return self
    def __exit__(self,*a):return False
    def geturl(self):return self.url
    def read(self,n):return self.raw

class Tests(unittest.TestCase):
    def setUp(self):
        self.day=datetime.now(mod.JST).strftime('%Y%m%d')
        self.url=f'https://www.boatrace.jp/owpc/pc/race/racelist?hd={self.day}&jcd=01&rno=1'
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
    def test_html_saved_with_sha(self):
        data=mod.capture(self.url,self.tmp.name,opener=lambda req,timeout:FakeResponse(self.url))
        self.assertEqual(len(data['sha256']),64)
        self.assertFalse(data['formal_eligible'])
        self.assertEqual((Path(self.tmp.name)/(data['sha256']+'.html')).read_bytes(),b'<html>test</html>')
    def test_external_source_rejected(self):
        with self.assertRaises(ValueError):mod.capture(self.url.replace('www.boatrace.jp','example.org'),self.tmp.name)
    def test_mismatched_final_url_rejected(self):
        with self.assertRaises(ValueError):mod.capture(self.url,self.tmp.name,opener=lambda req,timeout:FakeResponse(self.url+'&rno=2'))
    def test_failure_forbidden_day(self):
        with self.assertRaises(ValueError):mod.capture(self.url.replace(self.day,'20200101'),self.tmp.name)
    def test_idempotent_html_content(self):
        op=lambda req,timeout:FakeResponse(self.url)
        a=mod.capture(self.url,self.tmp.name,opener=op)
        b=mod.capture(self.url,self.tmp.name,opener=op)
        self.assertEqual(a['sha256'],b['sha256'])
        self.assertEqual(len(list(Path(self.tmp.name).glob('*.html'))),1)
    def test_non_html_rejected(self):
        x=FakeResponse(self.url);x.headers={'Content-Type':'application/json'}
        with self.assertRaises(ValueError):mod.capture(self.url,self.tmp.name,opener=lambda req,timeout:x)
    def test_redirect_handler_refuses(self):
        with self.assertRaises(ValueError):mod.NoRedirect().redirect_request(None,None,302,'Found',{},'https://example.org')

if __name__=='__main__':unittest.main()
