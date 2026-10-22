import json,unittest
from datetime import datetime,timedelta,timezone
from evaluate import TRIPLES,evaluate
def row(day,split,actual="1-2-3"):
    rates={t:1/120 for t in TRIPLES}
    date=f"2026-10-{day}"
    return dict(race_code=date.replace("-","")+"1201",deadline_jst=date+"T18:00:00+09:00",captured_at_jst=date+"T08:00:00+09:00",source_sha256="a"*64,split=split,outcome=actual,baseline_probs=json.dumps(rates),candidate_probs=json.dumps(rates))
class EvalTests(unittest.TestCase):
    def test_common_evaluation(self):
        x=evaluate([row("21","train"),row("22","test")]);self.assertEqual(x["n"],1)
    def test_missing_race(self):
        with self.assertRaises(ValueError):evaluate([row("22","test")])
    def test_late_capture(self):
        x=row("22","test");x["captured_at_jst"]="2026-10-22T17:50:00+09:00"
        with self.assertRaises(ValueError):evaluate([row("21","train"),x])
    def test_duplicate(self):
        x=row("22","test")
        with self.assertRaises(ValueError):evaluate([row("21","train"),x,x])
    def test_bad_probability(self):
        x=row("22","test");x["candidate_probs"]=json.dumps({"1-2-3":1})
        with self.assertRaises(ValueError):evaluate([row("21","train"),x])
    def test_date_leak(self):
        with self.assertRaises(ValueError):evaluate([row("22","train"),row("21","test")])
if __name__=="__main__":unittest.main()
