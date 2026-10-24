"""End-to-end offline verified start order ingestion checks."""
import datetime as dt
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parent))
from ingest_verified_start_order import ingest
from apply_pre_result_enrichment import write_new_snapshot
from validate_pre_result_enrichment import JST

RACE={"race_key":"20261025-04-01","meta":{"date":"2026-10-25","venue_code":"04","race_no":1,"deadline":"10:52","phase":"PRE_RESULT","results_seen":False,"unlock":False,"scoring":False},"racers":[{"lane":i,"registration_no":str(4000+i)} for i in range(1,7)]}
RAW=('<html><table><tr><th>コース</th><th>並び</th><th>ST</th></tr>'+''.join(f'<tr><td>{i}</td><td>{[2,1,3,4,5,6][i-1]}</td><td>.12</td></tr>' for i in range(1,7))+'</table></html>').encode()
AUDIT={"race_key":RACE["race_key"],"kind":"official_beforeinfo_html","status":"ok","source":"https://www.boatrace.jp/owpc/pc/race/beforeinfo?hd=20261025&jcd=04&rno=1","fetched_at":"2026-10-25T10:40:00+09:00","sha256":hashlib.sha256(RAW).hexdigest(),"bytes":len(RAW)}
NOW=dt.datetime(2026,10,25,10,45,tzinfo=JST)

class IngestionTests(unittest.TestCase):
    def test_ingest_and_write_new_only(self):
        snapshot=ingest(RACE,RAW,AUDIT,now=NOW)
        self.assertEqual(snapshot["actual_entry"],[2,1,3,4,5,6])
        self.assertEqual(snapshot["source_audit"]["actual_entry"]["sha256"],AUDIT["sha256"])
        self.assertEqual(snapshot["meta"],RACE["meta"])
        self.assertNotIn("actual_entry",RACE)
        with tempfile.TemporaryDirectory() as tmp:
            target=Path(tmp)/"new.json"
            write_new_snapshot(target,snapshot)
            self.assertEqual(json.loads(target.read_text())["actual_entry"],[2,1,3,4,5,6])
            with self.assertRaises(FileExistsError):write_new_snapshot(target,snapshot)
    def test_tampering_blocks_ingest(self):
        with self.assertRaisesRegex(ValueError,"source_verification_failed"):
            ingest(RACE,RAW+b"corrupt",AUDIT,now=NOW)
    def test_missing_boat_data_blocks_ingest(self):
        no_order=b"<html><table><tr><th>ST</th></tr></table></html>"
        manifest=dict(AUDIT,sha256=hashlib.sha256(no_order).hexdigest(),bytes=len(no_order))
        with self.assertRaisesRegex(ValueError,"actual_entry_not_explicit"):
            ingest(RACE,no_order,manifest,now=NOW)
    def test_already_recorded_entry_blocks_ingest(self):
        race=dict(RACE,actual_entry=[1,2,3,4,5,6])
        with self.assertRaisesRegex(ValueError,"replacement forbidden"):
            ingest(race,RAW,AUDIT,now=NOW)

if __name__=="__main__":
    unittest.main()
