"""Integration tests for archived HTML -> verified entry candidate."""
import datetime as dt
import hashlib
import sys
from pathlib import Path
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parent))
from build_verified_entry_candidate import candidate
from validate_pre_result_enrichment import JST

RACE={"race_key":"20261025-04-01","meta":{"date":"2026-10-25","venue_code":"04","race_no":1,"deadline":"10:52","phase":"PRE_RESULT","results_seen":False,"unlock":False,"scoring":False},"racers":[{"registration_no":str(4001+i)} for i in range(6)]}
RAW=('<html><table><tr><th>コース</th><th>並び</th><th>ST</th></tr>'+
''.join(f'<tr><td>{i}</td><td>{[2,1,3,4,5,6][i-1]}</td><td>.12</td></tr>' for i in range(1,7))+
'</table></html>').encode()
AUDIT={"race_key":RACE["race_key"],"kind":"official_beforeinfo_html","status":"ok","source":"https://www.boatrace.jp/owpc/pc/race/beforeinfo?hd=20261025&jcd=04&rno=1","fetched_at":"2026-10-25T10:40:00+09:00","sha256":hashlib.sha256(RAW).hexdigest(),"bytes":len(RAW)}
NOW=dt.datetime(2026,10,25,10,45,tzinfo=JST)

class VerifiedCandidateTests(unittest.TestCase):
    def test_valid_candidate(self):
        self.assertEqual(candidate(RAW,AUDIT,RACE,now=NOW)["actual_entry"],[2,1,3,4,5,6])
    def test_invalid_html_digest(self):
        with self.assertRaisesRegex(ValueError,"source_verification_failed"):
            candidate(RAW+b"x",AUDIT,RACE,now=NOW)
    def test_missing_explicit_labels(self):
        raw=RAW.replace(b"<td>2</td><td>1</td>",b"<td>2</td><td></td>")
        audit=dict(AUDIT,sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
        with self.assertRaisesRegex(ValueError,"actual_entry_not_explicit"):
            candidate(raw,audit,RACE,now=NOW)
    def test_deadline_source_rejected(self):
        with self.assertRaisesRegex(ValueError,"source_verification_failed"):
            candidate(RAW,dict(AUDIT,fetched_at="2026-10-25T10:53:00+09:00"),RACE,now=NOW)

if __name__=="__main__": unittest.main()
