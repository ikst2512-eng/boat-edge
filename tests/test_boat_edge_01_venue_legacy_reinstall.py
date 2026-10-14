"""V169/V170 scheduled display jobs must not overwrite tracked source.

Read-only fixture/source checks: no network, race results, or formal targets.
"""
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
WORKFLOWS=ROOT/'.github'/'workflows'


class SiteTrackedVenueSourceContracts(unittest.TestCase):
    def test_old_reinstallers_are_retired_and_report_jobs_remain(self):
        jobs=(
            ('BOAT_EDGE_V169_ONE_UPLOAD.yml',
             'V169_TRACKED_SOURCES_NO_LEGACY_REINSTALL_PASS',
             "cron: '15 0 * * *'",
             'python3 scripts/site_racer_venue_v169.py .',
             'data/site_racer_venue_v169/'),
            ('BOAT_EDGE_V170_ONE_UPLOAD.yml',
             'V170_TRACKED_SOURCES_NO_LEGACY_REINSTALL_PASS',
             "cron: '13 0-14 * * *'",
             'python3 scripts/site_mode_venue_v170.py',
             'data/site_learning/mode_venue_accuracy_v170.json'),
        )
        for name,marker,cron,compute,out in jobs:
            with self.subTest(name=name):
                source=(WORKFLOWS/name).read_text(encoding='utf-8')
                self.assertIn('workflow_dispatch:',source)
                self.assertIn(cron,source)
                self.assertIn(marker,source)
                self.assertIn('git ls-files --error-unmatch',source)
                self.assertNotIn('gzip.decompress',source)
                self.assertNotIn('base64.b64decode',source)
                self.assertNotIn('dest.write_bytes(',source)
                self.assertNotIn('path.write_bytes(',source)
                self.assertIn(compute,source)
                self.assertIn(out,source)
                self.assertIn("github.ref == 'refs/heads/main'",source)
                self.assertNotIn('git push --force',source)
                self.assertNotIn('git push -f',source)

    def test_existing_site_venue_imports_are_one_each(self):
        html=(ROOT/'index.html').read_text(encoding='utf-8')
        paths=(
            './assets/boat_edge_v169_venue_stats.css?v=169',
            './assets/boat_edge_v169_venue_stats.js?v=169',
            './assets/boat_edge_v170_venue_accuracy.css?v=170',
            './assets/boat_edge_v170_venue_accuracy.js?v=170',
        )
        for path in paths:
            with self.subTest(path=path):
                self.assertEqual(html.count(path),1)
        for path in (
            'scripts/site_racer_venue_v169.py',
            'tests/test_site_racer_venue_v169.py',
            'assets/boat_edge_v169_venue_stats.css',
            'assets/boat_edge_v169_venue_stats.js',
            'scripts/site_mode_venue_v170.py',
            'tests/test_site_mode_venue_v170.py',
            'assets/boat_edge_v170_venue_accuracy.css',
            'assets/boat_edge_v170_venue_accuracy.js',
        ):
            with self.subTest(path=path):
                self.assertTrue((ROOT/path).is_file())


if __name__=='__main__':
    unittest.main()
