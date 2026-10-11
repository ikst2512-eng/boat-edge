"""V243 regression: CSS-only iPhone legibility, with prediction logic untouched."""
import json
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


class TestV243MobileSite(unittest.TestCase):
    def read(self,name):
        return (ROOT/name).read_text(encoding="utf-8")

    def test_three_column_racer_metrics_are_readable(self):
        css=self.read('assets/boat_edge_v203_readable.css')
        v243=css.split('/* V243: readable iPhone racer metrics;',1)[1]
        self.assertIn('grid-template-columns:repeat(3,minmax(0,1fr))',v243)
        self.assertIn('grid-template-columns:repeat(2,minmax(0,1fr))',v243)
        self.assertIn('.be203-name b{font-size:14px',v243)
        self.assertIn('.be203-metrics small{font-size:10px',v243)
        self.assertIn('.be203-actions button{min-height:44px',v243)
        self.assertNotIn('display:none',v243)
        self.assertIn('.be203-metrics b.be203-red',css)
        self.assertIn('.be203-stats',css)

    def test_prediction_tickets_preserve_odds_and_stakes(self):
        css=self.read('assets/boat_edge_v204_prediction.css')
        self.assertIn('V243: maintain every prediction row',css)
        self.assertIn('.be204-ticket-finance b{font-size:13px',css)
        self.assertIn('.be204-unverified{font-size:12px',css)
        self.assertIn('.be108-ticket>small{font-size:12px',css)
        self.assertIn('.be108-ticket>b{font-size:18px',css)
        self.assertIn('.be204-ticket-finance',css)
        self.assertIn('be204-odds-unverified',css)
        v243=css.split('/* V243: maintain every prediction row',1)[1].split('/* V204 odds guard:',1)[0]
        self.assertNotIn('display:none',v243)

    def test_live_page_loads_both_style_layers_once(self):
        html=self.read('index.html')
        for filename in ('boat_edge_v203_readable.css?v=203','boat_edge_v204_prediction.css?v=204'):
            self.assertEqual(html.count(filename),1)
        self.assertLess(html.index('boat_edge_v203_readable.css'),html.index('boat_edge_v204_prediction.css'))

    def test_pre_result_formal_guards_remain_closed(self):
        state=json.loads(self.read('data/formal_status.json'))
        g=state.get('guards') or {}
        self.assertTrue(all(g.get(k) is False for k in ('results_seen','unlock','scoring')))
        self.assertIsNone(g.get('RESULT_UNLOCK_TOKEN'))


if __name__=='__main__':
    unittest.main()
