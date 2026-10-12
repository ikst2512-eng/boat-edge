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
    racers='<table>'+''.join(f'<tr><td>{i}</td><td>6.{i:02d} 0.0</td></tr>' for i in range(1,7))+'</table>'
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
    def test_never_rewrites_snapshot(self):
        m.write_json(self.root/'data/today.json',{'date':'2026-10-11','venues':[{'races':[{'race_key':KEY,'deadline':'14:43'}]}]})
        p=self.root/'data/site_prediction_snapshots'/f'{KEY}.json';p.parent.mkdir(parents=True);p.write_bytes(b'IMMUTABLE')
        self.assertEqual(m.targets(self.root,self.now),[])
        self.assertEqual(p.read_bytes(),b'IMMUTABLE')
    def test_parse_exact_six_registrations(self):
        self.assertEqual(set(m.parse_regs(htmlregs())),{str(1000+i) for i in range(1,7)})
        self.assertEqual(len(m.parse_before(htmlbefore())['racers']),6)
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
            html.replace('<td>6</td><td>6.06 0.0', '<td>6</td><td>-- 0.0',1),
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
