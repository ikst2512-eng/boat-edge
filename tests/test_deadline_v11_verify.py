import hashlib, importlib.util, json, tempfile, unittest
from datetime import datetime, timezone, timedelta
from pathlib import Path
HERE=Path(__file__).resolve().parents[1]/'scripts/deadline_v9/verify_artifacts.py'
spec=importlib.util.spec_from_file_location('v11',HERE)
v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
class Tests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.day=datetime.now(v.JST).strftime('%Y%m%d')
        raw=b'<html>official dummy</html>';sha=hashlib.sha256(raw).hexdigest()
        folder=self.root/'snapshots'/self.day/'01';folder.mkdir(parents=True)
        (folder/(sha+'.html')).write_bytes(raw)
        url=f'https://www.boatrace.jp/owpc/pc/race/racelist?hd={self.day}&jcd=01&rno=3'
        date=datetime.now(v.JST).isoformat()
        self.r={'date_jst':self.day,'results_seen':False,'formal_eligible':False,'errors':[],
          'captures':[{'venue_code':'01','race_number_requested':3,'sha256':sha,'bytes':len(raw),
          'source_url':url,'final_url':url,'capture_started_at_jst':date,'capture_finished_at_jst':date,
          'formal_eligible':False,'race_deadlines_verified':False}]}
        self.report=self.root/'report.json'
    def check(self):
        self.report.write_text(json.dumps(self.r))
        return v.verify(self.root,self.report)
    def test_valid_fixture_research_only(self):
        x=self.check();self.assertEqual(x['status'],'CAPTURE_INTEGRITY_PASS_RESEARCH_ONLY');self.assertFalse(x['formal_eligible'])
    def test_hash_tampered(self):
        path=next((self.root/'snapshots').rglob('*.html'));path.write_text('tampered');self.assertEqual(self.check()['status'],'LOCKED')
    def test_wrong_race_url(self):
        self.r['captures'][0]['race_number_requested']=4;self.assertEqual(self.check()['status'],'LOCKED')
    def test_duplicate(self):
        self.r['captures'].append(dict(self.r['captures'][0]));self.assertEqual(self.check()['status'],'LOCKED')
    def test_capture_error(self):
        self.r['errors']=[{'venue':'01','race_number_requested':7,'error':'timeout'}];self.assertEqual(self.check()['status'],'LOCKED')
    def test_formal_claim_rejected(self):
        self.r['captures'][0]['formal_eligible']=True;self.assertEqual(self.check()['status'],'LOCKED')
if __name__=='__main__':unittest.main()
