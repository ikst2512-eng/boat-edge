"""Regression: V215 must retain all simultaneous prospective race observations."""
import datetime as dt
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import boat_edge_v215_readiness as v215


class WindowCoverageTest(unittest.TestCase):
    def test_more_than_32_races_reach_current_and_history(self):
        now=dt.datetime(2026,10,18,0,0,tzinfo=dt.timezone.utc)
        day=now.astimezone(v215.JST).strftime('%Y%m%d')
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            rows=[{'race_key':f'{day}-{venue:02d}-{race:02d}',
                   'venue':'test','deadline':'09:05','minutes_left':5,
                   'reason':'snapshot_missing','source_gaps':['beforeinfo_not_ok']}
                  for venue in range(1,5) for race in range(1,11)]
            state={'schema':v215.SCHEMA,'scope':'PRE_RESULT_SITE_DIAGNOSTIC_NOT_FORMAL_FRESH',
                   'day_jst':day,'schedule_source_today':True,'scheduled_races':40,
                   'window_races':40,'reason_counts':{'snapshot_missing':40},
                   'current_window':rows,'next_race':None,'upcoming':[],
                   'source_counts_in_window':{},'checked_at':now.isoformat(),
                   'not_a_purchase_or_proven_accuracy':True}
            with patch.object(v215,'audit',return_value=state):
                v215.run(root,now)
            hist=json.loads((root/'data/site_paper_sim/readiness_history_v215'/
                             f'{day}.json').read_text())
            self.assertEqual(len(hist['observations']),40)
            self.assertEqual(hist['observations'][rows[-1]['race_key']]['observed_checks'],1)
            self.assertEqual(state['day_observed_races'],40)

    def test_audit_does_not_truncate_current_window(self):
        import inspect
        source=inspect.getsource(v215.audit)
        self.assertNotIn('window[:32]',source)
        self.assertIn("'current_window':window",source)


if __name__=='__main__':
    unittest.main()
