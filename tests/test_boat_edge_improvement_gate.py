import json
import tempfile
import unittest
from pathlib import Path
from scripts.boat_edge_improvement_gate import inspect

class ImprovementGateTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.root=Path(self.tmp.name)
        (self.root/"data/site_autopilot").mkdir(parents=True)
        self.save("data/formal_status.json",{"guards":{"results_seen":False,"unlock":False,"scoring":False,"RESULT_UNLOCK_TOKEN":None}})
        self.save("data/health.json",{"race_cards_total":100,"race_cards_ok":95,"beforeinfo_targets":10,"beforeinfo_ok":10,"original_exhibition_urgent_15m_missing":0})
        self.save("data/site_autopilot/v230_fast_current.json",{"fetch_wall_seconds":4,"freeze_wall_seconds":2,"network_error":0,"odds_incomplete":0})
    def tearDown(self):
        self.tmp.cleanup()
    def save(self,p,obj):
        (self.root/p).write_text(json.dumps(obj),encoding="utf-8")
    def test_healthy_is_observe(self):
        r=inspect(self.root)
        self.assertEqual(r["decision"],"OBSERVE")
        self.assertEqual(r["warnings"],[])
    def test_low_coverage_is_warning_not_formal_override(self):
        self.save("data/health.json",{"race_cards_total":100,"race_cards_ok":20,"beforeinfo_targets":10,"beforeinfo_ok":2,"original_exhibition_urgent_15m_missing":1})
        r=inspect(self.root)
        self.assertEqual(r["decision"],"OBSERVE")
        self.assertIn("RACE_CARD_LOW_COVERAGE",r["warnings"])
        self.assertIn("ORIGINAL_EXHIBITION_MISSING",r["warnings"])
        self.assertFalse(r["formal_certified"])
    def test_lock_break_fails_closed(self):
        self.save("data/formal_status.json",{"guards":{"results_seen":True,"unlock":False,"scoring":False,"RESULT_UNLOCK_TOKEN":None}})
        self.assertEqual(inspect(self.root)["decision"],"FAIL_CLOSED")
    def test_missing_status_fails_closed(self):
        (self.root/"data/formal_status.json").unlink()
        self.assertIn("FORMAL_STATUS_MISSING",inspect(self.root)["blockers"])
    def test_slow_fast_lane_is_diagnostic_only(self):
        self.save("data/site_autopilot/v230_fast_current.json",{"fetch_wall_seconds":80,"freeze_wall_seconds":20,"network_error":1,"odds_incomplete":1})
        r=inspect(self.root)
        self.assertIn("FETCH_STAGE_SLOW",r["warnings"])
        self.assertIn("FREEZE_STAGE_SLOW",r["warnings"])
        self.assertEqual(r["decision"],"OBSERVE")

if __name__=="__main__":
    unittest.main()
