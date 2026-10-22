import json, unittest
from feature_intake import ingest
def fixture():
    return {"race_code":"202610231201","boats":[{"boat":i,"actual_entry":i,"exhibition_st":0.11,"lap_time":37.1,"turn_time":6.5,"straight_time":7.7} for i in range(1,7)]}
class IntakeTests(unittest.TestCase):
    def run_ok(self,raw=None,at="2026-10-23T08:00:00+09:00",margin=12):
        obj=raw if raw is not None else fixture()
        return ingest(obj,json.dumps(obj).encode(),at,"2026-10-23T18:00:00+09:00",margin)
    def test_valid(self):
        p=self.run_ok();self.assertTrue(p["exhibition_complete"]);self.assertEqual(len(p["boats"]),6)
    def test_no_exhibition_keeps_entry(self):
        obj=fixture()
        for b in obj["boats"]:del b["exhibition_st"]
        p=self.run_ok(obj);self.assertFalse(p["exhibition_complete"])
    def test_duplicate_entry(self):
        obj=fixture();obj["boats"][1]["actual_entry"]=1
        with self.assertRaises(ValueError):self.run_ok(obj)
    def test_duplicate_boat(self):
        obj=fixture();obj["boats"][1]["boat"]=1
        with self.assertRaises(ValueError):self.run_ok(obj)
    def test_late(self):
        with self.assertRaises(ValueError):self.run_ok(at="2026-10-23T17:49:00+09:00")
    def test_wrong_offset(self):
        with self.assertRaises(ValueError):self.run_ok(at="2026-10-23T08:00:00+08:00")
    def test_no_source(self):
        with self.assertRaises(ValueError):ingest(fixture(),b"", "2026-10-23T08:00:00+09:00","2026-10-23T18:00:00+09:00")
    def test_bad_measurement(self):
        obj=fixture();obj["boats"][3]["exhibition_st"]="0.15"
        with self.assertRaises(ValueError):self.run_ok(obj)
if __name__=="__main__":unittest.main()
