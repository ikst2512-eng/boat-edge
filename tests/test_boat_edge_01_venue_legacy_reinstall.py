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
             "cron: '13 0,13 * * *'",
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

    def test_v170_research_only_bounded_daily_fallback(self):
        source=(WORKFLOWS/'BOAT_EDGE_V170_ONE_UPLOAD.yml').read_text(encoding='utf-8')
        events=source.split('on:',1)[1].split('permissions:',1)[0]
        self.assertIn("cron: '13 0,13 * * *'", events)
        self.assertEqual(events.count('cron:'),1)
        self.assertIn("data/site_learning/mode_accuracy_v136.json", events)
        self.assertIn('  workflow_dispatch:',events)
        self.assertIn('  push:',events)
        self.assertIn('production_prediction_weights_changed', (ROOT/'scripts/site_mode_venue_v170.py').read_text(encoding='utf-8'))
        self.assertIn("git add -- data/site_learning/mode_venue_accuracy_v170.json",source)
        self.assertNotIn('gh workflow run',source)
        self.assertNotIn('data/formal_results',source)

    def test_venue_jobs_cannot_rewrite_main_ui_or_source(self):
        # V169/V170 historical report jobs are not 03-owned UI installers.
        rules=(
            ('BOAT_EDGE_V169_ONE_UPLOAD.yml',
             'V169_TRACKED_SITE_IMPORTS_READ_ONLY_PASS',
             'git add -- data/site_racer_venue_v169/',
             'git diff --exit-code -- index.html'),
            ('BOAT_EDGE_V170_ONE_UPLOAD.yml',
             'V170_TRACKED_SITE_IMPORTS_READ_ONLY_PASS',
             'git add -- data/site_learning/mode_venue_accuracy_v170.json',
             'git diff --exit-code -- index.html'),
        )
        for file,marker,staging,guard in rules:
            with self.subTest(file=file):
                workflow=(WORKFLOWS/file).read_text(encoding='utf-8')
                self.assertIn(marker,workflow)
                self.assertIn(staging,workflow)
                self.assertIn(guard,workflow)
                self.assertNotIn('p.write_text(data,encoding=',workflow)
                self.assertNotIn('p.write_text(s,encoding=',workflow)
                self.assertNotIn('git add -- index.html',workflow)
                self.assertNotIn(' index.html\n',workflow.split('git add --',1)[-1])
                # Source edits may only happen through PRs, never scheduled jobs.
                self.assertNotIn('git add scripts/site_mode_venue_v170.py',workflow)
                self.assertNotIn('git add -- index.html assets/',workflow)

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
