"""Regression for V215 full near-deadline counters vs eight-row preview."""
import datetime as dt
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from scripts import boat_edge_v215_readiness as v215


class V215CountersTest(unittest.TestCase):
    def test_all_near_deadline_races_counted_beyond_preview_cap(self):
        now=dt.datetime(2026,10,18,0,0,tzinfo=dt.timezone.utc)
        day=now.astimezone(v215.JST).strftime('%Y%m%d')
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            venues=[]
            for n in range(1,13):
                key=f'{day}-01-{n:02d}'
                venues.append({'race_key':key,'deadline':'09:05'})
                path=root/'data/races'/f'{key}.json'
                path.parent.mkdir(parents=True,exist_ok=True)
                path.write_text(json.dumps({'source_audit':{
                    'race_card':{'status':'ok'},'beforeinfo':{'status':'ok'}}}))
            path=root/'data/today.json'
            path.parent.mkdir(parents=True,exist_ok=True)
            path.write_text(json.dumps({'date':day,'venues':[{'venue':'test','races':venues}]}))
            with patch.object(v215,'due_for',return_value=now+dt.timedelta(minutes=5)), \
                 patch.object(v215,'source_gaps',return_value=[]):
                out=v215.audit(root,now)
            self.assertEqual(out['window_races'],12)
            self.assertEqual(len(out['current_window']),12)
            self.assertEqual(len(out['upcoming']),8)
            self.assertEqual(out['source_counts_in_window']['race_card_ok'],12)
            self.assertEqual(out['source_counts_in_window']['beforeinfo_ok'],12)


if __name__=='__main__':
    unittest.main()
