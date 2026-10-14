"""V156 must publish evidence changes, not volatile run timestamps.

Offline synthetic git repository, no race results or formal source access.
"""
import json
from pathlib import Path
import subprocess
import tempfile
import textwrap
import unittest

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / '.github/workflows/BOAT_EDGE_V156_FRESH_WATCH.yml'
PATH = Path('data/site_racer_actual_course/v156_watch/audit.json')


def inline_script():
    source = WORKFLOW.read_text(encoding='utf-8')
    prefix = "          python3 - <<'PY_V156_NO_TIMESTAMP_CHURN'\n"
    assert source.count(prefix) == 1, 'V156_INLINE_SCRIPT_NOT_UNIQUE'
    body = source.split(prefix, 1)[1].split(
        '\n          PY_V156_NO_TIMESTAMP_CHURN', 1)[0]
    return textwrap.dedent(body) + '\n'


def git(root, *args):
    return subprocess.run(
        ['git', *args], cwd=root, check=True, text=True,
        capture_output=True).stdout


def write(root, doc):
    target = root / PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(doc, sort_keys=True, indent=2) + '\n', encoding='utf-8')
    return target.read_bytes()


class V156MeaningfulEvidenceOnly(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        git(self.root, 'init', '-q')
        git(self.root, 'config', 'user.email', 'fixture@example.test')
        git(self.root, 'config', 'user.name', 'Fixture')
        self.base = {
            'schema_version': 'boat-edge-v156-prospective-evidence-watch-v1',
            'generated_at_utc': '2026-10-15T00:10:00+00:00',
            'status': 'FROZEN_WAITING_SETTLEMENT',
            'frozen_races': 6,
            'scored_races': 0,
            'formal_2026_10_08_result_accessed': False,
            'formal_unlock': False,
            'formal_scoring': False,
        }
        self.old_bytes = write(self.root, self.base)
        git(self.root, 'add', str(PATH))
        git(self.root, 'commit', '-qm', 'first verified research report')

    def check_script(self):
        result = subprocess.run(
            ['python3', '-c', inline_script()], cwd=self.root,
            check=False, text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return result.stdout

    def test_timestamp_only_update_retains_exact_committed_bytes(self):
        later = dict(self.base, generated_at_utc='2026-10-15T01:10:00+00:00')
        write(self.root, later)
        self.assertIn('V156_TIMESTAMP_ONLY_UNCHANGED_NO_PAGES_COMMIT', self.check_script())
        self.assertEqual((self.root / PATH).read_bytes(), self.old_bytes)
        self.assertEqual(git(self.root, 'status', '--porcelain'), '')

    def test_meaningful_evidence_must_still_publish(self):
        changed = dict(self.base, generated_at_utc='2026-10-15T01:10:00+00:00',
                       scored_races=6, status='PROSPECTIVE_MONITORING_NO_PROMOTION')
        updated = write(self.root, changed)
        self.assertIn('V156_MEANINGFUL_EVIDENCE_CHANGED_PUBLISH', self.check_script())
        self.assertEqual((self.root / PATH).read_bytes(), updated)
        self.assertNotEqual(git(self.root, 'status', '--porcelain'), '')

    def test_report_is_only_staged_path_and_v155_schedule_untouched(self):
        source = WORKFLOW.read_text(encoding='utf-8')
        self.assertIn("cron: '16 23 * * *'", source)
        self.assertIn("cron: '15 0 * * *'", source)
        self.assertIn('git add data/site_racer_actual_course/v156_watch/audit.json', source)
        self.assertNotIn('git add data/site_racer_actual_course/v155_fresh', source)
        self.assertIn('if k!=\'generated_at_utc\'', inline_script())
        self.assertNotIn('formal_results/', inline_script())


if __name__ == '__main__':
    unittest.main()
