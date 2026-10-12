import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class V289ExhibitionEvidence(unittest.TestCase):
    def test_six_numeric_exhibition_times_required(self):
        js = (ROOT / "assets/boat_edge_v223_source_visibility.js").read_text(encoding="utf-8")
        self.assertIn("before.racers.length===6", js)
        self.assertIn("before.racers.every(x=>typeof x?.exhibition_time==='number'", js)
        self.assertNotIn("before.start_exhibition.length===6", js)

    def test_browser_cache_invalidation(self):
        html = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn("boat_edge_v223_source_visibility.js?v=223&amp;rev=244&amp;patch=250&amp;source=282&amp;fix=329", html)

if __name__ == "__main__":
    unittest.main()
