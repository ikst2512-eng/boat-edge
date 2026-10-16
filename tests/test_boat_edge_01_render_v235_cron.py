"""Validate a staged (not provisioned) independent V235 scheduler Blueprint."""
from pathlib import Path
import unittest
import yaml

ROOT = Path(__file__).resolve().parents[1]


class ExternalCronBlueprintSafety(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = yaml.safe_load((ROOT / 'render.yaml').read_text(encoding='utf-8'))
        cls.service = cls.config['services'][0]

    def test_exact_single_external_cron_no_duplicate_writer(self):
        self.assertEqual(len(self.config['services']), 1)
        self.assertEqual(self.service['type'], 'cron')
        self.assertEqual(self.service['name'], 'boat-edge-v235-gap-backup')
        self.assertEqual(self.service['runtime'], 'python')
        self.assertEqual(self.service['branch'], 'main')

    def test_jst_hours_and_2_minute_backup_outside_github_schedule(self):
        self.assertEqual(self.service['schedule'], '*/2 23,0-13 * * *')
        self.assertEqual(self.service['region'], 'singapore')
        self.assertEqual(self.service['autoDeployTrigger'], 'off')

    def test_default_off_even_with_paid_service_and_token(self):
        vars_by_key = {v['key']: v for v in self.service['envVars']}
        self.assertEqual(set(vars_by_key),
                         {'BOAT_EDGE_GITHUB_ACTIONS_TOKEN', 'BOAT_EDGE_EXTERNAL_V235_ENABLED'})
        self.assertIs(vars_by_key['BOAT_EDGE_GITHUB_ACTIONS_TOKEN']['sync'], False)
        self.assertNotIn('value', vars_by_key['BOAT_EDGE_GITHUB_ACTIONS_TOKEN'])
        self.assertEqual(vars_by_key['BOAT_EDGE_EXTERNAL_V235_ENABLED']['value'], 'false')
        self.assertIn('boat_edge_01_v235_external_gap_watchdog.py --live',
                      self.service['startCommand'])
        self.assertIn('test_boat_edge_01_v235_external_gap_watchdog.py',
                      self.service['buildCommand'])

    def test_no_new_github_owner_or_model_modification(self):
        workflow = (ROOT / '.github/workflows/V235.yml').read_text(encoding='utf-8')
        self.assertIn('  workflow_dispatch:', workflow.split('permissions:', 1)[0])
        self.assertNotIn('BOAT_EDGE_EXTERNAL_V235_ENABLED', workflow)


if __name__ == '__main__':
    unittest.main()
