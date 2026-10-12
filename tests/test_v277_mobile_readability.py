import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class MobileRaceReadabilityV277(unittest.TestCase):
    def test_css_is_linked_in_head(self):
        html = (ROOT / "index.html").read_text(encoding="utf-8")
        link = "boat_edge_v277_mobile_readability.css?v=277"
        self.assertEqual(html.count(link), 1)
        self.assertLess(html.index(link), html.index("</head>"))

    def test_existing_race_dom_anchors(self):
        html = (ROOT / "index.html").read_text(encoding="utf-8")
        for element in ("raceView", "raceTabs", "tab-pred", "tab-before", "tab-data", "tab-card"):
            self.assertIn('id="' + element + '"', html)

    def test_mobile_css_scoped_to_race_view(self):
        css = (ROOT / "assets/boat_edge_v277_mobile_readability.css").read_text(encoding="utf-8")
        self.assertIn("@media (max-width: 760px)", css)
        self.assertIn("#raceView #raceTabs", css)
        self.assertIn("#tab-before .tablewrap", css)
        self.assertIn("overflow-x: auto", css)

if __name__ == "__main__":
    unittest.main()
