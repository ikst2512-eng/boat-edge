from datetime import datetime,timedelta,timezone
import json
from pathlib import Path
import tempfile
import unittest
from scripts.boat_edge_v01_catalog_continuity import should_keep_verified_same_day_catalog

JST=timezone(timedelta(hours=9))
NOW=datetime(2026,10,17,4,0,tzinfo=JST)

def fixtures(root):
    folder=root/'data'
    (folder/'races').mkdir(parents=True)
    races=[]
    for no in range(1,13):
        key=f'20261017-01-{no:02d}'
        (folder/'races'/f'{key}.json').write_text(
            json.dumps({'race_key':key,'meta':{'phase':'PRE_RESULT'}}),encoding='utf8')
        races.append({'race_key':key,'race_no':no,'deadline':'15:26',
                      'file':f'data/races/{key}.json'})
    old={'schema_version':'boat-edge-today-v5','date':'2026-10-17',
         'updated_at':'2026-10-17T03:40:24+09:00','phase':'PRE_RESULT',
         'results_seen':False,'unlock':False,'scoring':False,
         'collector_version':'BOAT_EDGE_V18','collector':{'active_venues':1},
         'venues':[{'jcd':'01','races':races}]}
    new={'date':'2026-10-17','phase':'PRE_RESULT','results_seen':False,
         'unlock':False,'scoring':False,'venues':[]}
    path=folder/'today.json'
    path.write_text(json.dumps(old),encoding='utf8')
    return path,old,new

class SameDayContinuity(unittest.TestCase):
    def test_real_0343_to_0400_empty_discovery_preserves_exact_source_timestamp(self):
        with tempfile.TemporaryDirectory() as td:
            path,old,new=fixtures(Path(td))
            before=path.read_bytes()
            self.assertTrue(should_keep_verified_same_day_catalog(path,new,NOW))
            self.assertEqual(path.read_bytes(),before)
            self.assertEqual(json.loads(before)['updated_at'],old['updated_at'])

    def test_same_day_0545_and_0825_retain_schedule_without_forging_freshness(self):
        # Production 2026-10-17 catalog was last verified at 03:40 JST.
        # Do not erase 168 scheduled races after the former 90min TTL.
        with tempfile.TemporaryDirectory() as td:
            path,old,new=fixtures(Path(td))
            original=path.read_bytes()
            for hour,minute in ((5,45),(8,25),(18,45),(23,59)):
                current=datetime(2026,10,17,hour,minute,tzinfo=JST)
                self.assertTrue(should_keep_verified_same_day_catalog(path,new,current))
                self.assertEqual(path.read_bytes(),original)
                self.assertEqual(json.loads(path.read_bytes())['updated_at'],
                                 '2026-10-17T03:40:24+09:00')
            # The same catalog cannot carry forward into another race day.
            next_day=datetime(2026,10,18,0,1,tzinfo=JST)
            self.assertFalse(should_keep_verified_same_day_catalog(
                path,{**new,'date':'2026-10-18'},next_day))
            # A future-dated or 2+ day-old catalog must not pass.
            old['updated_at']='2026-10-19T01:00:00+09:00'
            path.write_text(json.dumps(old),encoding='utf8')
            self.assertFalse(should_keep_verified_same_day_catalog(
                path,new,datetime(2026,10,17,5,45,tzinfo=JST)))

    def test_real_updated_nonempty_source_is_never_blocked(self):
        with tempfile.TemporaryDirectory() as td:
            path,old,new=fixtures(Path(td))
            self.assertFalse(should_keep_verified_same_day_catalog(path,{**new,'venues':old['venues']},NOW))
            self.assertFalse(should_keep_verified_same_day_catalog(path,{**new,'unlock':True},NOW))
            self.assertFalse(should_keep_verified_same_day_catalog(path,{**new,'date':'2026-10-16'},NOW))

    def test_stale_malformed_and_result_unsafe_catalog_fail_closed(self):
        with tempfile.TemporaryDirectory() as td:
            path,old,new=fixtures(Path(td))
            for mutation in (
                {'date':'2026-10-16'},{'results_seen':True},{'scoring':True},
                {'updated_at':'2026-10-16T23:59:00+09:00'},
                {'updated_at':'2026-10-17T04:02:00+09:00'},
                {'venues':[]},{'collector':{'active_venues':0}},
            ):
                path.write_text(json.dumps({**old,**mutation}),encoding='utf8')
                self.assertFalse(should_keep_verified_same_day_catalog(path,new,NOW),mutation)
            broken=json.loads(json.dumps(old))
            broken['venues'][0]['races'][0]['race_key']='20261017-02-01'
            path.write_text(json.dumps(broken),encoding='utf8')
            self.assertFalse(should_keep_verified_same_day_catalog(path,new,NOW))
            path.write_text(json.dumps(old),encoding='utf8')
            (Path(td)/'data/races/20261017-01-01.json').unlink()
            self.assertFalse(should_keep_verified_same_day_catalog(path,new,NOW))

    def test_symlink_catalog_fail_closed(self):
        with tempfile.TemporaryDirectory() as td:
            path,old,new=fixtures(Path(td))
            other=Path(td)/'data/source.json'
            other.write_text(json.dumps(old),encoding='utf8')
            path.unlink()
            path.symlink_to(other)
            self.assertFalse(should_keep_verified_same_day_catalog(path,new,NOW))

    def test_existing_collector_remains_only_writer_with_stale_health(self):
        wf=(Path(__file__).resolve().parents[1]/'.github/workflows/auto-update.yml').read_text(encoding='utf8')
        self.assertIn('from scripts.boat_edge_v01_catalog_continuity import should_keep_verified_same_day_catalog',wf)
        self.assertIn('if should_keep_verified_same_day_catalog(DATA/"today.json",summary,now):',wf)
        self.assertIn('V01_SAME_DAY_CATALOG_PRESERVED_SOURCE_UNAVAILABLE',wf)
        self.assertIn('(DATA/"today.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding="utf-8")',wf)
        self.assertIn('"source_unavailable"',wf)
        self.assertIn('git add -A data/',wf)

if __name__=='__main__':
    unittest.main()
