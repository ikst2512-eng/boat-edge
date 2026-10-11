import json
import os
import tempfile
import unittest
from datetime import datetime, timezone, timedelta
from pathlib import Path
from unittest.mock import patch
from scripts import site_odds_v167_live_audit as runner
from test_site_odds_v167 import build_sample

DATE='2026-10-09'
class Clock:
    @staticmethod
    def now(tz=None): return datetime(2026,10,9,16,0,tzinfo=tz)
class Response:
    status_code=200
    encoding='utf-8'
    apparent_encoding='utf-8'
    def __init__(self,txt):self.text=txt
    def raise_for_status(self):pass
class Session:
    headers={}
    def __init__(self,txt):self.txt=txt
    def get(self,*a,**k):return Response(self.txt)
class RunnerTest(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.was=os.getcwd();os.chdir(self.tmp.name)
        Path('.github/workflows').mkdir(parents=True)
        Path('.github/workflows/site-odds.yml').write_text('foo\n'+runner.MARKER+'bar\n')
        Path('data').mkdir()
        Path('data/today.json').write_text(json.dumps({'date':DATE,'venues':[
            {'jcd':'01','races':[{'race_key':'20261009-01-02','race_no':2,'deadline':'16:20'}]},
            {'jcd':'02','races':[{'race_key':'20261009-02-03','race_no':3,'deadline':'16:30'}]}]}))
    def tearDown(self):os.chdir(self.was);self.tmp.cleanup()
    def _run(self,source):
        with patch.object(runner,'datetime',Clock),patch.object(runner.requests,'Session',lambda:Session(source)),patch.object(runner.time,'sleep',lambda x:None):
            runner.run()
    def test_promotion_only_after_two_120_verified(self):
        self._run(build_sample())
        s=json.loads(Path('data/site_odds/verification_v167.json').read_text())
        self.assertEqual(s['status'],'TWO_LIVE_RACES_120_PARITY_PASS')
        self.assertEqual([x['checked'] for x in s['samples']],[120,120])
        self.assertIn('verify_official_dom_price_mapping(html)',Path('.github/workflows/site-odds.yml').read_text())
    def test_no_promotion_on_structural_mismatch(self):
        self._run(build_sample(incorrect=True))
        s=json.loads(Path('data/site_odds/verification_v167.json').read_text())
        self.assertEqual(s['status'],'FAIL_UNVERIFIED_NO_COLLECTOR_CHANGE')
        self.assertFalse(s['collector_guard_promoted'])
        self.assertNotIn('verify_official_dom_price_mapping(html)',Path('.github/workflows/site-odds.yml').read_text())
    def test_no_promotion_when_one_live_venue(self):
        s=json.loads(Path('data/today.json').read_text());s['venues']=s['venues'][:1]
        Path('data/today.json').write_text(json.dumps(s))
        self._run(build_sample())
        v=json.loads(Path('data/site_odds/verification_v167.json').read_text())
        self.assertEqual(v['status'],'WAITING_TWO_LIVE_VENUES')
        self.assertFalse(v['collector_guard_promoted'])
if __name__=='__main__':unittest.main()
