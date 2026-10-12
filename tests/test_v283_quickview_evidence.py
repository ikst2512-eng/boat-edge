import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class QuickviewEvidenceV283(unittest.TestCase):
    def test_no_acquired_claim_without_pre_result_guards(self):
        source = (ROOT / "assets/boat_edge_v206_quickview.js").read_text(encoding="utf-8")
        start = source.index("const source=(r,k)=>{")
        end = source.index("const tabs=", start)
        section = source[start:end]
        self.assertIn("phase!=='PRE_RESULT'", section)
        self.assertIn("results_seen!==false", section)
        self.assertIn("unlock!==false", section)
        self.assertIn("scoring!==false", section)
        self.assertLess(section.index("results_seen!==false"), section.index("const x=r?.source_audit?.[k]"))
        self.assertIn("締切後取得・未確認", section)
        self.assertIn("古い情報", section)

    def test_cache_bust_link(self):
        html = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertEqual(html.count("boat_edge_v206_quickview.js?v=283"), 1)

if __name__ == "__main__":
    unittest.main()
