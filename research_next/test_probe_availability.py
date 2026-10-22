import io,tempfile,unittest
from datetime import datetime,timezone,timedelta
from unittest.mock import Mock,MagicMock
from probe_availability import run_probe
JST=timezone(timedelta(hours=9))
CODE="202610231201"
URL="https://boatracecsv.github.io/data/programs/race_cards/2026/10/23.csv"
def fake(body):
    response=Mock()
    response.status=200
    response.read.return_value=body
    response.geturl.return_value=URL
    response.__enter__=Mock(return_value=response)
    response.__exit__=Mock(return_value=False)
    return lambda *args,**kw:response
def csv_body(code=CODE):
    return ("レースコード,"+",".join(f"艇{i}_全国勝率" for i in range(1,7))+"\n"+code+",6,6,6,6,6,6\n").encode()
class ProbeTests(unittest.TestCase):
    def test_valid_before_cutoff(self):
        at=datetime(2026,10,23,17,47,tzinfo=JST)
        with tempfile.TemporaryDirectory() as d:
            result=run_probe(CODE,"2026-10-23T18:00:00+09:00",URL,d,clock=lambda:at,opener=fake(csv_body()))
            self.assertEqual(result["eligible_margins"],[12,11,10])
            self.assertTrue(result["target_race_validated"])
    def test_missing_race_rejected(self):
        at=datetime(2026,10,23,17,47,tzinfo=JST)
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError):
                run_probe(CODE,"2026-10-23T18:00:00+09:00",URL,d,clock=lambda:at,opener=fake(csv_body("202610231202")))
    def test_wrong_day_source_rejected(self):
        at=datetime(2026,10,23,17,47,tzinfo=JST)
        bad=URL.replace("/23.csv","/22.csv")
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError):
                run_probe(CODE,"2026-10-23T18:00:00+09:00",bad,d,clock=lambda:at,opener=fake(csv_body()))
    def test_title_deadline_mismatch_rejected(self):
        at=datetime(2026,10,23,17,47,tzinfo=JST)
        title=URL.replace("/race_cards/","/title/")
        body="レースコード,電話投票締切予定\\n202610231201,18:01\\n".encode()
        response=MagicMock()
        response.status=200
        response.read.return_value=body
        response.geturl.return_value=title
        response.__enter__.return_value=response
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError):
                run_probe(CODE,"2026-10-23T18:00:00+09:00",title,d,clock=lambda:at,opener=lambda *a,**kw:response)
    def test_late_not_eligible(self):
        at=datetime(2026,10,23,17,51,tzinfo=JST)
        with tempfile.TemporaryDirectory() as d:
            result=run_probe(CODE,"2026-10-23T18:00:00+09:00",URL,d,clock=lambda:at,opener=fake(csv_body()))
            self.assertEqual(result["eligible_margins"],[])
if __name__=="__main__":unittest.main()
