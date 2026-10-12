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

    def test_race_switch_resets_safety_and_source_labels(self):
        source = (ROOT / "assets/boat_edge_v206_quickview.js").read_text(encoding="utf-8")
        self.assertIn("lastTable='';lastStatus='';", source)
        self.assertIn("!$('.be206-safety strong',box)?.textContent", source)
        self.assertIn("直前データ証跡", source)
        self.assertIn("オリ展証跡", source)
        self.assertIn("6艇分の値・外部照合・予想利用は別途確認", source)
        self.assertNotIn("公式展示 ${source(", source)

    def test_six_boat_completeness_is_numeric_only(self):
        source = (ROOT / "assets/boat_edge_v206_quickview.js").read_text(encoding="utf-8")
        self.assertIn("sixBoatCount=(items,valid)", source)
        self.assertIn("items.length<=6", source)
        self.assertIn("before.racers", source)
        self.assertIn("orig.boats", source)
        self.assertIn("numericPresent(x?.exhibition_time)", source)
        self.assertIn("Array.isArray(x?.values)", source)
        self.assertIn("数値の存在は取得元・鮮度・独立照合の証明ではありません", source)

    def test_completeness_uses_deadline_aware_source_evidence(self):
        source = (ROOT / "assets/boat_edge_v206_quickview.js").read_text(encoding="utf-8")
        start = source.index("const completeness=r=>{")
        end = source.index("const tabs=", start)
        section = source[start:end]
        self.assertIn("source(r,'beforeinfo')", section)
        self.assertIn("source(r,'original_exhibition')", section)
        self.assertNotIn("audit[k]?.status==='ok'?'証跡あり'", section)

    def test_rebuilds_six_boat_table_after_dom_replacement(self):
        source = (ROOT / "assets/boat_edge_v206_quickview.js").read_text(encoding="utf-8")
        self.assertIn("lastTable!==data||(layout==='lanes'?!$('.be206-matrix tbody',box):!$('.be206-table tbody',box))", source)
        self.assertIn("innerHTML=format(rows)", source)
        self.assertIn("innerHTML=matrix(rows)", source)

    def test_partial_six_boat_arrays_are_not_zeroed(self):
        source = (ROOT / "assets/boat_edge_v206_quickview.js").read_text(encoding="utf-8")
        self.assertIn("items.length<=6", source)
        self.assertNotIn("items.length===6?\\n items.filter(valid).length:0", source)

    def test_cache_bust_link(self):
        html = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertEqual(html.count("boat_edge_v206_quickview.js?v=321"), 1)

if __name__ == "__main__":
    unittest.main()
