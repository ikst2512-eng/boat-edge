"""V245: paper-only stale-day display and formal lock regression."""
import json
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

class TestV245PaperDay(unittest.TestCase):
 def test_old_day_cannot_appear_as_current_budget(self):
  js=(ROOT/'assets/boat_edge_v211_paper.js').read_text()
  for x in ("proof.current?remaining.toLocaleString('ja-JP')+'円':'―'",
            "proof.current?yen(spent):'―'",
            "proof.current?m.today_paper_races+'R':'―'",
            "!proof.current?'本日台帳未確認'",
            "proof.current&&d.strategy_status==='PAPER_ACTIVE'",
            "過去の保存台帳（本日未確認）"):
   self.assertIn(x,js)
  self.assertNotIn("today_remaining_yen??m.daily_budget_yen??50000",js)
 def test_original_source_money_only_and_formal_locked(self):
  js=(ROOT/'assets/boat_edge_v211_paper.js').read_text()
  self.assertIn("m.today_spent_yen+m.today_remaining_yen!==m.daily_budget_yen",js)
  self.assertIn("m?.virtual_only!==true",js)
  self.assertNotIn("data/formal_",js)
  state=json.loads((ROOT/'data/formal_status.json').read_text())
  g=state.get('guards') or {}
  self.assertTrue(all(g.get(k) is False for k in ('results_seen','unlock','scoring')))
  self.assertIsNone(g.get('RESULT_UNLOCK_TOKEN'))
if __name__=='__main__':unittest.main()
