"""Fixture-only protection of the existing site's controlled Pages packaging."""
from pathlib import Path
import tempfile
import unittest

from scripts.site_pages_stage import copy_public_tree


class SitePagesStageTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve()
        sample = {
            "index.html": b"index",
            "autopilot.html": b"autopilot",
            ".nojekyll": b"",
            "assets/boat_edge_v108.js": b"script",
            "assets/extra.css": b"css",
            "data/today.json": b"today",
            "data/formal_status.json": b"closed formal status only",
            "data/races/20261014-01-01.json": b"pre-result race fixture",
            "data/site_results/20261013-01-01.json": b"site-only confirmed fixture",
            "data/site_prediction_snapshots/a.json": b"site source first-add fixture",
            "data/raw/20261014/01_01_beforeinfo.html": b"raw not for Pages",
            "data/formal_predictions/hidden.json": b"restricted formal",
            "scripts/internal.py": b"do not publish code",
            ".github/workflows/other.yml": b"not published",
        }
        for name, data in sample.items():
            file = self.root / name
            file.parent.mkdir(parents=True, exist_ok=True)
            file.write_bytes(data)

    def test_only_existing_public_surface_is_staged_byte_exact(self):
        total = copy_public_tree(self.root, self.root / "_pages_site")
        self.assertGreater(total, 8)
        out = self.root / "_pages_site"
        for path in (
            "index.html", "autopilot.html", ".nojekyll",
            "assets/boat_edge_v108.js", "assets/extra.css", "data/today.json",
            "data/formal_status.json", "data/races/20261014-01-01.json",
            "data/site_results/20261013-01-01.json",
            "data/site_prediction_snapshots/a.json",
        ):
            self.assertEqual((out / path).read_bytes(), (self.root / path).read_bytes())
        for hidden in (
            "data/raw", "data/formal_predictions", "scripts", ".github"
        ):
            self.assertFalse((out / hidden).exists(), hidden)

    def test_missing_mandatory_feed_fails_closed(self):
        (self.root / "data/today.json").unlink()
        with self.assertRaisesRegex(ValueError, "Missing"):
            copy_public_tree(self.root, self.root / "_pages_site")

    def test_symlink_in_public_assets_fails_closed(self):
        outside = self.root / "scripts/internal.py"
        link = self.root / "assets/bad.js"
        link.symlink_to(outside)
        with self.assertRaisesRegex(ValueError, "Symlink"):
            copy_public_tree(self.root, self.root / "_pages_site")

    def test_refuse_arbitrary_output_directory(self):
        with self.assertRaisesRegex(ValueError, "Output must"):
            copy_public_tree(self.root, self.root / "data")


if __name__ == "__main__":
    unittest.main()
