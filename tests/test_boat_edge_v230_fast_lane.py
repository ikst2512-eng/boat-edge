from __future__ import annotations
from datetime import datetime,timedelta,timezone
from pathlib import Path
import json
import tempfile
import unittest
from unittest.mock import patch, Mock

import boat_edge_v230_fast_lane as m

JST=m.JST
KEY='20261011-06-08'

def makerace(dl='14:43'):
    return {'race_key':KEY,'meta':{'date':'2026-10-11','deadline':dl,'race_no':8,'venue_code':'06',
                                 'phase':'PRE_RESULT','results_seen':False,'unlock':False,'scoring':False},
            'racers':[{'lane':i,'registration_no':str(1000+i),'raw_text':f'{1000+i} / A1'} for i in range(1,7)],
            'source_audit':{}}

def htmlregs(scratch=False):
    content=''.join(f'<tr><td>{i}</td><td>{1000+i} / A1</td></tr>' for i in range(1,7))
    return '<table>'+content+'</table>'+('欠場' if scratch else '')

def htmlbefore():
    racers='<table><tr><th>展示タイム</th></tr>'+''.join(f'<tr><td>{i}</td><td>選手</td><td>体重</td><td>6.71 前走情報</td><td>6.{i:02d}</td><td>0.0</td></tr>' for i in range(1,7))+'</table>'
    # Mirror the classed spans in the actual official START-display table.
    starts='<table><tr><th>スタート展示</th></tr><tr><td>'+''.join(
       '<div class="table1_boatImage1"><span class="table1_boatImage1Number">'
       +str(i)+'</span><span class="table1_boatImage1Time">.12</span></div>'
       for i in range(1,7))+'</td></tr></table>'
    return racers+starts

class FastLaneTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
        (self.root/'data/races').mkdir(parents=True)
        m.write_json(self.root/'data/races'/f'{KEY}.json',makerace())
        self.now=datetime(2026,10,11,14,36,tzinfo=JST)
    def tearDown(self):self.tmp.cleanup()
    def data(self,scratch=False):
        return {'racelist':(htmlregs(scratch).encode(),htmlregs(scratch),self.now),
                'beforeinfo':(htmlbefore().encode(),htmlbefore(),self.now),
                'odds':(b'official-odds-byte', '<html>...</html>',self.now)}
    def test_selects_window_only(self):
        m.write_json(self.root/'data/today.json',{'date':'2026-10-11','venues':[{'races':[{'race_key':KEY,'deadline':'14:43'}]}]})
        self.assertEqual(m.targets(self.root,self.now),[KEY])
    def test_refuses_past_and_future(self):
        m.write_json(self.root/'data/today.json',{'date':'2026-10-11','venues':[{'races':[{'race_key':KEY,'deadline':'14:43'}]}]})
        self.assertEqual(m.targets(self.root,self.now+timedelta(minutes=6)),[])
        self.assertEqual(m.targets(self.root,self.now-timedelta(minutes=18)),[])
    def test_zero_target_diagnostic_is_read_only(self):
        m.write_json(self.root/'data/today.json',{'date':'2026-10-11','venues':[{'races':[{'race_key':KEY,'deadline':'14:43'}]}]})
        self.assertEqual(m.target_diagnostic(self.root,self.now)['eligible'],1)
        self.assertEqual(m.target_diagnostic(self.root,self.now-timedelta(minutes=18))['outside_2_to_19_min_window'],1)
        self.assertEqual(m.target_diagnostic(self.root,self.now+timedelta(minutes=6))['outside_2_to_19_min_window'],1)
        self.assertEqual(m.targets(self.root,self.now),[KEY])
        self.assertEqual(m.target_diagnostic(self.root,self.now.replace(day=12))['today_mismatch'],1)

    def test_naruto_20261014_0820_preflight_and_strict_freeze_window(self):
        # Exact priority race: source collection starts before the 2-10 minute
        # V229 freeze window. This only verifies scheduling/identity, not a
        # published official beforeinfo value or a saved prediction.
        key='20261014-14-01'
        self.assertEqual(key,'20261014-14-01')
        m.write_json(self.root/'data/today.json',{'date':'2026-10-14',
            'venues':[{'venue':'鳴門','races':[{'race_key':key,'deadline':'08:35'}]}]})
        race=makerace('08:35')
        race['race_key']=key
        race['meta'].update(date='2026-10-14',race_no=1,venue_code='14')
        m.write_json(self.root/'data/races'/f'{key}.json',race)
        def at(hour,minute):return datetime(2026,10,14,hour,minute,tzinfo=JST)
        self.assertEqual(m.targets(self.root,at(8,15)),[])
        self.assertEqual(m.target_diagnostic(self.root,at(8,15))['outside_2_to_19_min_window'],1)
        for hour,minute in ((8,20),(8,22),(8,25),(8,27),(8,32),(8,33)):
            with self.subTest(clock=f'{hour:02d}:{minute:02d}'):
                self.assertEqual(m.targets(self.root,at(hour,minute)),[key])
                self.assertEqual(m.target_diagnostic(self.root,at(hour,minute))['eligible'],1)
        # V230 source prewarming must not be confused with V229 eligibility:
        # 08:20 / 08:22 are too early for the immutable FINAL_15M freeze.
        self.assertGreater((m.due_for(key,'08:35')-at(8,20)).total_seconds(),600)
        self.assertGreater((m.due_for(key,'08:35')-at(8,22)).total_seconds(),600)
        for minute in (25,27,32,33):
            self.assertTrue(120 <= (m.due_for(key,'08:35')-at(8,minute)).total_seconds() <= 600)
        self.assertEqual(m.targets(self.root,at(8,34)),[])
        self.assertEqual(m.targets(self.root,at(8,35)),[])
        snap=self.root/'data/site_prediction_snapshots'/f'{key}.json'
        self.assertFalse(snap.exists(),'preflight must not write or backfill a prediction')

    def test_naruto_priority_isolates_source_fetch_only_during_decision_window(self):
        # 08:27: Naruto's deadline is 08:35; Tokuyama 1R at 08:43 is
        # also eligible for V230. Slow Tokuyama requests must not delay the
        # owner-priority Naruto snapshot and first Git commit.
        naruto='20261014-14-01'
        tokuyama='20261014-18-01'
        today={'date':'2026-10-14','venues':[
            {'venue':'鳴門','races':[{'race_key':naruto,'deadline':'08:35'}]},
            {'venue':'徳山','races':[{'race_key':tokuyama,'deadline':'08:43'}]}]}
        m.write_json(self.root/'data/today.json',today)
        for key,venue,deadline in ((naruto,'14','08:35'),
                                   (tokuyama,'18','08:43')):
            race=makerace(deadline)
            race['race_key']=key
            race['meta'].update(date='2026-10-14',venue_code=venue,race_no=1)
            m.write_json(self.root/'data/races'/f'{key}.json',race)
        def fake_fetch(root,key):
            return key,{'verified_mock':'no_official_network'},None
        at=lambda h,minute:datetime(2026,10,14,h,minute,tzinfo=JST)
        with (patch('boat_edge_v228_freeze_only.check_formal_closed'),
              patch('boat_edge_v229_atomic_freeze.run',return_value=0),
              patch.object(m,'fetch_one',side_effect=fake_fetch) as fetch,
              patch.object(m,'update_one',return_value='fresh_verified')):
            first=m.run(self.root,at(8,27),worker=2,priority_key=naruto)
            self.assertEqual(first['targets'],[naruto])
            self.assertTrue(first['priority_applied'])
            self.assertEqual(fetch.call_count,1)
            self.assertEqual(fetch.call_args.args[1],naruto)
            fetch.reset_mock()
            later=m.run(self.root,at(8,37),worker=2,priority_key=naruto)
            self.assertEqual(later['targets'],[tokuyama])
            self.assertFalse(later['priority_applied'])
            self.assertEqual(fetch.call_count,1)
            self.assertEqual(fetch.call_args.args[1],tokuyama)

    def test_imminent_retry_only_for_incomplete_source_not_explicit_scratch(self):
        m.write_json(self.root/'data/today.json',{'date':'2026-10-11',
            'venues':[{'races':[{'race_key':KEY,'deadline':'14:43'}]}]})
        odds={KEY:'odds_incomplete'}
        self.assertEqual(m.imminent_retry_targets(self.root,[KEY],odds,self.now),[KEY])
        self.assertEqual(m.imminent_retry_targets(
            self.root,[KEY],odds,self.now-timedelta(minutes=4)),[])
        self.assertEqual(m.imminent_retry_targets(
            self.root,[KEY],odds,self.now+timedelta(minutes=6)),[])
        scratch={'race_key':KEY,'blocked':True,
                 'official_beforeinfo_six_boat_complete':False,
                 'suspect_lanes':[],'official_raw_flags':[],
                 'reason':'公式直前情報の展示データを検証できない'}
        m.write_json(self.root/'data/site_scratches_v182'/f'{KEY}.json',scratch)
        self.assertEqual(m.imminent_retry_targets(
            self.root,[KEY],{KEY:'source_blocked'},self.now),[KEY])
        scratch['suspect_lanes']=[3]
        m.write_json(self.root/'data/site_scratches_v182'/f'{KEY}.json',scratch)
        self.assertEqual(m.imminent_retry_targets(
            self.root,[KEY],{KEY:'source_blocked'},self.now),[])
        scratch['suspect_lanes']=[]
        scratch['official_raw_flags']=['racelist']
        m.write_json(self.root/'data/site_scratches_v182'/f'{KEY}.json',scratch)
        self.assertEqual(m.imminent_retry_targets(
            self.root,[KEY],{KEY:'source_blocked'},self.now),[])
        self.assertEqual(m.imminent_retry_targets(
            self.root,[KEY],{KEY:'fresh_verified'},self.now),[])

    def test_imminent_retry_keeps_first_snapshot_immutable(self):
        m.write_json(self.root/'data/today.json',{'date':'2026-10-11',
            'venues':[{'races':[{'race_key':KEY,'deadline':'14:43'}]}]})
        path=self.root/'data/site_prediction_snapshots'/f'{KEY}.json'
        path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(b'IMMUTABLE')
        self.assertEqual(m.imminent_retry_targets(
            self.root,[KEY],{KEY:'odds_incomplete'},self.now),[])
        self.assertEqual(path.read_bytes(),b'IMMUTABLE')

    def test_imminent_retry_performs_second_official_fetch_and_atomic_freeze(self):
        m.write_json(self.root/'data/today.json',{'date':'2026-10-11',
            'venues':[{'races':[{'race_key':KEY,'deadline':'14:43'}]}]})
        with (patch('boat_edge_v228_freeze_only.check_formal_closed'),
              patch('boat_edge_v229_atomic_freeze.run',side_effect=[0,1]) as frozen,
              patch.object(m,'fetch_one',return_value=(KEY,{'fixture':True},None)) as fetched,
              patch.object(m,'update_one',side_effect=['odds_incomplete','fresh_verified']) as updated,
              patch.object(m,'local_now',return_value=self.now),
              patch.object(m.time,'sleep') as paused):
            status=m.run(self.root,now=self.now,worker=2,retry_imminent=True)
        self.assertEqual(fetched.call_count,2)
        self.assertEqual(updated.call_count,2)
        self.assertEqual(frozen.call_count,2)
        paused.assert_called_once_with(20)
        self.assertEqual(status['imminent_retry_targets'],[KEY])
        self.assertEqual(status['imminent_retry_snapshots'],1)
        self.assertEqual(status['new_snapshots_atomic_audited'],1)
        self.assertEqual(status['source_refreshed'],1)
        self.assertEqual(status['odds_incomplete'],0)

    def test_successful_first_freeze_is_never_delayed_by_retry(self):
        m.write_json(self.root/'data/today.json',{'date':'2026-10-11',
            'venues':[{'races':[{'race_key':KEY,'deadline':'14:43'}]}]})
        with (patch('boat_edge_v228_freeze_only.check_formal_closed'),
              patch('boat_edge_v229_atomic_freeze.run',return_value=1) as frozen,
              patch.object(m,'fetch_one',return_value=(KEY,{'fixture':True},None)) as fetched,
              patch.object(m,'update_one',return_value='odds_incomplete'),
              patch.object(m,'local_now',return_value=self.now),
              patch.object(m.time,'sleep') as paused):
            status=m.run(self.root,now=self.now,worker=2,retry_imminent=True)
        self.assertEqual(status['new_snapshots_atomic_audited'],1)
        self.assertEqual(status['imminent_retry_targets'],[])
        frozen.assert_called_once()
        fetched.assert_called_once()
        paused.assert_not_called()

    def test_never_rewrites_snapshot(self):
        m.write_json(self.root/'data/today.json',{'date':'2026-10-11','venues':[{'races':[{'race_key':KEY,'deadline':'14:43'}]}]})
        p=self.root/'data/site_prediction_snapshots'/f'{KEY}.json';p.parent.mkdir(parents=True);p.write_bytes(b'IMMUTABLE')
        self.assertEqual(m.targets(self.root,self.now),[])
        self.assertEqual(p.read_bytes(),b'IMMUTABLE')
    def test_parse_exact_six_registrations(self):
        self.assertEqual(set(m.parse_regs(htmlregs())),{str(1000+i) for i in range(1,7)})
        self.assertEqual(len(m.parse_before(htmlbefore())['racers']),6)
    def test_v294_no_fake_exhibition_from_other_racer_cells(self):
        orig=htmlbefore()
        missing=orig.replace('<td>6.03</td><td>0.0</td>', '<td>--</td><td>0.0</td>',1)
        parsed=m.parse_before(missing)
        self.assertIsNone(parsed['racers'][2]['exhibition_time'])
        self.assertFalse(m.beforeinfo_coverage(parsed)['six_boat_complete'])
        # 6.71 "previous race" text and similar tilt-like tokens are not
        # permission to impute the actual exhibition time.
        bad_all=orig.replace('<td>6.01</td><td>0.0</td>', '<td>未公開</td><td>0.0</td>',1)
        self.assertIsNone(m.parse_before(bad_all)['racers'][0]['exhibition_time'])
        badtilt=orig.replace('<td>6.01</td><td>0.0</td>', '<td>6.01</td><td>未公開</td>',1)
        self.assertIsNone(m.parse_before(badtilt)['racers'][0]['tilt'])
        verified=m.parse_before(orig)
        self.assertEqual(verified['racers'][0]['exhibition_time'],6.01)
        self.assertEqual(verified['racers'][0]['tilt'],0.0)

    def test_v289_does_not_mistake_six_stat_rows_for_exhibition(self):
        spoof='<table><tr><th>全国勝率</th></tr>'+''.join(
          f'<tr><td>{i}</td><td>6.79</td></tr>' for i in range(1,7))+'</table>'
        self.assertFalse(m.beforeinfo_coverage(m.parse_before(spoof))['six_boat_complete'])
        # A preceding unrelated 6.x table cannot manufacture six boats.
        p=m.parse_before(spoof+htmlbefore())
        self.assertEqual(len(p['racers']),6)
        self.assertTrue(m.beforeinfo_coverage(p)['six_boat_complete'])
        # Duplicate official exhibition tables are ambiguous even with 12 racers.
        self.assertEqual(m.parse_before(htmlbefore()+htmlbefore())['racers'],[])
        self.assertFalse(m.beforeinfo_coverage(m.parse_before(htmlbefore()+htmlbefore()))['six_boat_complete'])

    def test_v289_real_archived_official_start_and_exhibition(self):
        # Explicit PRE_RESULT HTML fixtures, not outcomes or historical results.
        repo=Path(__file__).resolve().parents[1]
        archived=[repo/p for p in ('data/raw/20261012/14_01_beforeinfo.html',
                                   'data/raw/20261012/01_03_beforeinfo.html')]
        # The main unit suite also runs in source-only sandbox checkouts.
        # The V288 official archived-HTML CI independently *requires* its
        # fixtures and fails if missing; this general suite uses them if present.
        archived=[p for p in archived if p.is_file()]
        if not archived:
            self.skipTest('Archival pre-result fixtures absent; V288 archival CI validates them')
        for path in archived:
            html=path.read_text(encoding='utf8')
            with self.subTest(path=path):
                parsed=m.parse_before(html)
                c=m.beforeinfo_coverage(parsed)
                self.assertTrue(c['six_boat_complete'],c)
                self.assertEqual(set(x['lane'] for x in parsed['start_exhibition']),set(range(1,7)))
                self.assertEqual(set(x['lane'] for x in parsed['racers']),set(range(1,7)))

    def test_v289_requires_exact_six_st_and_six_exhibition_lanes(self):
        html=htmlbefore()
        parsed=m.parse_before(html)
        full=m.beforeinfo_coverage(parsed)
        self.assertTrue(full['six_boat_complete'])
        self.assertEqual(full['start_exhibition_lanes'],6)
        self.assertEqual(full['exhibition_lanes'],6)
        for bad in (
            html.replace('class="table1_boatImage1Time">.12', 'class="table1_boatImage1Time">--',1),
            html.replace('class="table1_boatImage1Number">6', 'class="table1_boatImage1Number">5',1),
            html.replace('<td>6</td><td>選手</td><td>体重</td><td>6.71 前走情報</td><td>6.06', '<td>6</td><td>-- 0.0',1),
            html.replace('class="table1_boatImage1Time">.12', 'class="table1_boatImage1Time">.12</span></div><div class="table1_boatImage1"><span class="table1_boatImage1Number">1</span><span class="table1_boatImage1Time">.12',1)
        ):
            with self.subTest(bad=bad[:60]):
                self.assertFalse(m.beforeinfo_coverage(m.parse_before(bad))['six_boat_complete'])

    def test_v289_partial_beforeinfo_is_never_green_even_with_official_odds(self):
        prices={f'{a}-{b}-{c}':10.0 for a in range(1,7) for b in range(1,7) for c in range(1,7) if len({a,b,c})==3}
        bad=htmlbefore().replace('class="table1_boatImage1Time">.12', 'class="table1_boatImage1Time">--',1)
        proof=self.data()
        proof['beforeinfo']=(bad.encode(),bad,self.now)
        with patch.object(m,'verified_odds',return_value=prices):
            self.assertEqual(m.update_one(self.root,KEY,proof,self.now),'source_blocked')
        r=m.load(self.root/'data/races'/f'{KEY}.json')
        self.assertEqual(r['source_audit']['beforeinfo']['status'],'published_wait')
        self.assertFalse(r['source_audit']['beforeinfo']['six_boat_coverage']['six_boat_complete'])
        scratch=m.load(self.root/'data/site_scratches_v182'/f'{KEY}.json')
        self.assertTrue(scratch['blocked'])
        self.assertFalse(scratch['official_beforeinfo_six_boat_complete'])

    def test_mismatching_official_racers_rejects_and_leaves_original(self):
        original=(self.root/'data/races'/f'{KEY}.json').read_bytes()
        d=self.data();d['racelist']=(htmlregs().replace('1001','2001').encode(),htmlregs().replace('1001','2001'),self.now)
        with patch.object(m,'verified_odds',return_value={f'{a}-{b}-{c}':10.0 for a in range(1,7) for b in range(1,7) for c in range(1,7) if len({a,b,c})==3}):
            self.assertEqual(m.update_one(self.root,KEY,d,self.now),'six_registration_mismatch')
        self.assertEqual(original,(self.root/'data/races'/f'{KEY}.json').read_bytes())
    def test_verified_source_and_odds_written_once_from_exact_bytes(self):
        prices={f'{a}-{b}-{c}':10.0 for a in range(1,7) for b in range(1,7) for c in range(1,7) if len({a,b,c})==3}
        with patch.object(m,'verified_odds',return_value=prices):
            self.assertEqual(m.update_one(self.root,KEY,self.data(),self.now),'fresh_verified')
        r=m.load(self.root/'data/races'/f'{KEY}.json')
        self.assertEqual(r['source_audit']['beforeinfo']['status'],'ok')
        self.assertEqual(r['beforeinfo']['racers'][0]['exhibition_time'],6.01)
        o=m.load(self.root/'data/site_odds'/f'{KEY}.json')
        self.assertEqual(o['available_count'],120)
        self.assertEqual(o['raw_official_html_sha256'],m.sha(b'official-odds-byte'))
        import gzip
        self.assertEqual(gzip.decompress((self.root/'data/raw/20261011/06_08_odds3t.html.gz').read_bytes()),b'official-odds-byte')
        s=m.load(self.root/'data/site_scratches_v182'/f'{KEY}.json')
        self.assertIs(s['blocked'],False)
        self.assertEqual(s['official_beforeinfo_source_status'],'ok')
    def test_scratch_blocks_even_when_odds_pass(self):
        prices={f'{a}-{b}-{c}':10.0 for a in range(1,7) for b in range(1,7) for c in range(1,7) if len({a,b,c})==3}
        with patch.object(m,'verified_odds',return_value=prices):
            self.assertEqual(m.update_one(self.root,KEY,self.data(scratch=True),self.now),'source_blocked')
        self.assertIs(m.load(self.root/'data/site_scratches_v182'/f'{KEY}.json')['blocked'],True)
    def test_odds_unverified_never_forged(self):
        with patch.object(m,'verified_odds',side_effect=ValueError('DOM mismatch')):
            self.assertEqual(m.update_one(self.root,KEY,self.data(),self.now),'odds_incomplete')
        self.assertFalse((self.root/'data/site_odds'/f'{KEY}.json').exists())
    def test_v167_verification_fails_closed_without_labelled_dom(self):
        import types,sys
        self.assertIsNone(m.due_for('20261011-30-99','24:64'))
        with patch.dict(sys.modules,{'site_odds_v167_dom_verifier':types.SimpleNamespace(verify_official_dom_price_mapping=lambda h: (_ for _ in ()).throw(ValueError('bad DOM')))}):
            with self.assertRaises(ValueError):m.verified_odds('<td class="oddsPoint">10.2</td>')
    def test_official_odds_120_dom_mapping_when_v167_passes(self):
        import types,sys
        t=''.join('<tr>'+''.join(f'<td class="oddsPoint">{i*6+j+1}.0</td>' for j in range(6))+'</tr>' for i in range(20))
        html='<table>'+t+'</table>'
        proof=lambda h:{'status':'PASS','checked':120,'available':120}
        with patch.dict(sys.modules,{'site_odds_v167_dom_verifier':types.SimpleNamespace(verify_official_dom_price_mapping=proof)}):
            o=m.verified_odds(html)
        self.assertEqual(len(o),120)
        self.assertEqual(o['1-2-3'],1.0)
        self.assertEqual(o['2-1-3'],2.0)
    def test_write_raw_proof_binds_source(self):
        prices={f'{a}-{b}-{c}':10.0 for a in range(1,7) for b in range(1,7) for c in range(1,7) if len({a,b,c})==3}
        with patch.object(m,'verified_odds',return_value=prices):m.update_one(self.root,KEY,self.data(),self.now)
        raw=(self.root/'data/raw/20261011/06_08_racelist.html').read_bytes()
        r=m.load(self.root/'data/races'/f'{KEY}.json')
        self.assertEqual(m.sha(raw),r['source_audit']['race_card']['sha256'])

if __name__=='__main__':unittest.main()


class TransientOfficialFetchRetryTests(unittest.TestCase):
    """PRE_RESULT-only retries cannot weaken identity or outcome restrictions."""

    @staticmethod
    def fixture():
        return b'<html>official PRE_RESULT fixture</html>', 'official PRE_RESULT fixture', datetime(2026,10,14,8,25,tzinfo=JST)

    def test_one_transport_timeout_retries_same_official_url_then_succeeds(self):
        import requests
        sess=Mock();sess.headers=Mock()
        good=self.fixture()
        with patch('requests.Session',return_value=sess),patch('time.sleep') as nap,patch.object(
                m,'fetch',side_effect=[requests.exceptions.Timeout('slow'),good,good,good]) as call:
            key,data,error=m.fetch_one(Path('.'),'20261014-14-01')
        self.assertEqual(key,'20261014-14-01')
        self.assertIsNone(error)
        self.assertEqual(list(data),['racelist','beforeinfo','odds'])
        self.assertEqual(call.call_count,4)
        self.assertEqual(call.call_args_list[0],call.call_args_list[1])
        self.assertIn('hd=20261014',call.call_args_list[0].args[1])
        self.assertIn('jcd=14',call.call_args_list[0].args[1])
        self.assertIn('rno=1',call.call_args_list[0].args[1])
        nap.assert_called_once_with(0.35)
        sess.close.assert_called_once()

    def test_one_official_503_retries_only_failed_odds_url(self):
        import requests
        sess=Mock();sess.headers=Mock();good=self.fixture()
        temporary=requests.exceptions.HTTPError('503',response=Mock(status_code=503))
        with patch('requests.Session',return_value=sess),patch('time.sleep') as nap,patch.object(
                m,'fetch',side_effect=[good,good,temporary,good]) as call:
            key,data,error=m.fetch_one(Path('.'),'20261014-14-01')
        self.assertIsNone(error)
        self.assertEqual(call.call_count,4)
        self.assertEqual(call.call_args_list[2],call.call_args_list[3])
        self.assertIn('/odds3t?',call.call_args_list[2].args[1])
        nap.assert_called_once_with(0.35)
        sess.close.assert_called_once()

    def test_persistent_timeout_stops_after_two_and_never_forges_source(self):
        import requests
        sess=Mock();sess.headers=Mock()
        with patch('requests.Session',return_value=sess),patch('time.sleep') as nap,patch.object(
                m,'fetch',side_effect=[requests.exceptions.Timeout('first'),requests.exceptions.Timeout('again')]) as call:
            key,data,error=m.fetch_one(Path('.'),'20261014-14-01')
        self.assertIsNone(data)
        self.assertIn('Timeout',error)
        self.assertEqual(call.call_count,2)
        nap.assert_called_once_with(0.35)
        sess.close.assert_called_once()

    def test_redirect_and_nontransient_404_never_retried(self):
        import requests
        for bad in (RuntimeError('V278_REDIRECT_BLOCKED_BEFORE_FOLLOW'),
                    RuntimeError('V278_RESPONSE_RACE_IDENTITY_MISMATCH'),
                    requests.exceptions.HTTPError('404',response=Mock(status_code=404))):
            sess=Mock();sess.headers=Mock()
            with self.subTest(error=str(bad)),patch('requests.Session',return_value=sess),patch(
                    'time.sleep') as nap,patch.object(m,'fetch',side_effect=bad) as call:
                key,data,error=m.fetch_one(Path('.'),'20261014-14-01')
                self.assertIsNone(data)
                self.assertTrue(error)
                call.assert_called_once()
                nap.assert_not_called()
                sess.close.assert_called_once()


class SourceIdentityTests(unittest.TestCase):
    url='https://www.boatrace.jp/owpc/pc/race/beforeinfo?hd=20261013&jcd=06&rno=8'

    def session(self,url=None,status=200):
        response=Mock(status_code=status,url=url or self.url,content=b'fixture',
                      text='fixture',apparent_encoding='utf-8')
        session=Mock();session.get.return_value=response
        return session,response

    def test_exact_race_accepts_query_reordering(self):
        session,_=self.session(self.url.split('?')[0]+'?rno=08&jcd=06&hd=20261013')
        self.assertEqual(m.fetch(session,self.url)[:2],(b'fixture','fixture'))
        session.get.assert_called_once_with(self.url,timeout=(4,13),allow_redirects=False)

    def test_redirect_never_followed_or_decoded(self):
        for status in (301,302,303,307,308):
            session,r=self.session(status=status)
            with self.subTest(status=status),self.assertRaisesRegex(RuntimeError,'REDIRECT_BLOCKED'):
                m.fetch(session,self.url)
            session.get.assert_called_once_with(self.url,timeout=(4,13),allow_redirects=False)
            r.raise_for_status.assert_not_called()

    def test_wrong_response_identity_rejected(self):
        for old,new in [('20261013','20261012'),('jcd=06','jcd=07'),('rno=8','rno=9'),('beforeinfo','odds3t')]:
            session,_=self.session(self.url.replace(old,new))
            with self.subTest(new=new),self.assertRaises(RuntimeError):m.fetch(session,self.url)

    def test_invalid_request_is_rejected_before_network(self):
        urls=[self.url+'&rno=9',self.url+'&x=1',self.url.replace('rno=8','rno='),
              self.url.replace('rno=8','rno=13'),self.url.replace('jcd=06','jcd=00'),
              self.url.replace('20261013','20260230'),self.url+'#fragment',
              self.url.replace('www.boatrace.jp','www.boatrace.jp.evil.example'),
              self.url.replace('https:','http:'),self.url.replace('beforeinfo','raceresult')]
        for url in urls:
            session,_=self.session()
            with self.subTest(url=url),self.assertRaises(ValueError):m.fetch(session,url)
            session.get.assert_not_called()
