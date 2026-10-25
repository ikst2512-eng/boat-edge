"""Guard diagnostic-only official-card vs CSV-card gap counting."""
from pathlib import Path
import unittest

WORKFLOW = Path(__file__).resolve().parents[1] / ".github/workflows/auto-update.yml"

class Core7CardGapContract(unittest.TestCase):
    def test_observation_cannot_override_core7(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("if card_available and rc is None and all(source_presence.values()):", text)
        self.assertIn("core7_card_gap+=1", text)
        self.assertIn('"scope":"MUTABLE_PREDEADLINE_ONLY_NOT_FORMAL_ELIGIBILITY"', text)
        self.assertIn("and all(core7_boat(rc,stt,tkz,b) for b in range(1,7))", text)
        self.assertLess(text.index("if not source_write_allowed(DATA,race_key"),
                        text.index("core7_card_gap+=1"))
        self.assertIn('"formal_first100_ready":False', text)
        self.assertIn('"unlock":False,"scoring":False', text)

if __name__ == "__main__":
    unittest.main()
