"""Synthetic-only proof tests. Never fetch results, payouts or real races."""
from __future__ import annotations
import json
import hashlib
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import boat_edge_01_gate1c_source_ready as gate

JST=timezone(timedelta(hours=9))
AT=datetime(2026,10,16,8,28,tzinfo=JST)
KEY='20261016-14-01'

def put(root,sub,obj):
    p=root/sub
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(obj,ensure_ascii=False),encoding='utf8')
    return p

class ProspectiveReady(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        stamp=(AT-timedelta(minutes=2)).isoformat()
        # Genuine raw bytes must back both observed official SHA declarations.
        raw='a'*64
        self.raw_content={}
        for role in ('racelist','beforeinfo'):
            p=self.root/f'data/raw/20261016/14_01_{role}.html'
            p.parent.mkdir(parents=True,exist_ok=True)
            p.write_bytes(('<html>'+role+' official source</html>').encode())
            self.raw_content[role]=hashlib.sha256(p.read_bytes()).hexdigest()
        self.race={
            'race_key':KEY,
            'meta':{'date':'2026-10-16','venue_code':'14','race_no':1,
                    'deadline':'08:35','phase':'PRE_RESULT','results_seen':False,
                    'unlock':False,'scoring':False},
            'racers':[{}]*6,
            'source_audit':{
              'race_card':{'status':'ok','fetched_at':stamp,
                           'sha256':self.raw_content['racelist'],'source':'https://www.boatrace.jp/owpc/pc/race/racelist?hd=20261016&jcd=14&rno=1'},
              'beforeinfo':{'status':'ok','fetched_at':stamp,'sha256':self.raw_content['beforeinfo'],
                    'source':'https://www.boatrace.jp/owpc/pc/race/beforeinfo?hd=20261016&jcd=14&rno=1',
                    'six_boat_coverage':{'six_boat_complete':True}},
            }}
        self.scratch={'schema_version':'boat-edge-v182-scratch-evidence-v1',
            'race_key':KEY,'source_date':KEY[:8],
            'race_card_sha256':self.raw_content['racelist'],
            'beforeinfo_sha256':self.raw_content['beforeinfo'],
            'blocked':False,'checked_at':stamp,
            'race_card_source_status':'ok','official_beforeinfo_source_status':'ok',
            'official_beforeinfo_six_boat_complete':True,
            'suspect_lanes':[],'official_raw_flags':[]}
        self.odds={'race_key':KEY,'phase':'PRE_RESULT_PURCHASE_ONLY',
            'fetched_at':stamp,'available_count':120,
            'verified_official_dom_v167':True,'results_seen':False,'scoring':False,
            'trifecta_odds':{f'{a}-{b}-{c}':12.3 for a in range(1,7)
                for b in range(1,7) for c in range(1,7) if len({a,b,c})==3}}
        put(self.root,'data/today.json',
            {'date':'2026-10-16','venues':[{'venue':'鳴門','races':[{
                'race_key':KEY,'deadline':'08:35'}]}]})
        put(self.root,'data/formal_status.json',{'guards':{
            'results_seen':False,'unlock':False,'scoring':False,
            'RESULT_UNLOCK_TOKEN':None},'formalFirst100':{'races':0}})
        self.sources()

    def sources(self):
        put(self.root,f'data/races/{KEY}.json',self.race)
        put(self.root,f'data/site_scratches_v182/{KEY}.json',self.scratch)
        put(self.root,f'data/site_odds/{KEY}.json',self.odds)

    def test_ready_first_only_and_sha_capture(self):
        first=gate.run(self.root,AT)
        self.assertEqual(first['created'],[KEY])
        file=self.root/gate.OUT/f'{KEY}.json'
        proof=json.loads(file.read_text())
        self.assertEqual(proof['official_odds_combinations'],120)
        self.assertEqual(len(proof['source_sha256']),3)
        self.assertEqual(proof['observed_at'],AT.astimezone(timezone.utc).isoformat())
        self.assertFalse(proof['independently_eligible_denominator_established'])
        self.assertFalse(proof['first_git_source_commit_independently_proven'])
        original=file.read_bytes()
        self.odds['trifecta_odds']['1-2-3']=99
        self.sources()
        self.assertEqual(gate.run(self.root,AT+timedelta(seconds=15))['created'],[])
        self.assertEqual(file.read_bytes(),original)

    def test_missing_or_stale_official_inputs_do_not_fake_denominator(self):
        def check_failure():
            self.sources()
            out=gate.run(self.root,AT)
            self.assertEqual(out['created'],[])
            self.assertFalse((self.root/gate.OUT/f'{KEY}.json').exists())
        self.race['source_audit']['beforeinfo']['six_boat_coverage']['six_boat_complete']=False
        check_failure()
        self.race['source_audit']['beforeinfo']['six_boat_coverage']['six_boat_complete']=True
        self.scratch['blocked']=True
        check_failure()
        self.scratch['blocked']=False
        self.scratch['official_beforeinfo_six_boat_complete']=False
        check_failure()
        self.scratch['official_beforeinfo_six_boat_complete']=True
        self.odds['trifecta_odds']['1-2-3']=0
        check_failure()
        self.odds['trifecta_odds']['1-2-3']=12.3
        self.odds['verified_official_dom_v167']=False
        check_failure()
        self.odds['verified_official_dom_v167']=True
        self.race['source_audit']['beforeinfo']['source']='https://evil.example/beforeinfo'
        check_failure()

    def test_original_official_source_uri_must_identify_this_race(self):
        """Even an official URL for a different real race cannot count."""
        check=lambda: self.assertIsNone(gate.valid(
            self.root,KEY,gate.expected_deadline(KEY,'08:35'),AT))
        card=self.race['source_audit']['race_card']
        before=self.race['source_audit']['beforeinfo']
        self.assertIsNotNone(gate.valid(
            self.root,KEY,gate.expected_deadline(KEY,'08:35'),AT))
        base=card['source']
        for invalid in (
            'https://www.boatrace.jp/owpc/pc/race/racelist?hd=20261016&jcd=14&rno=2',
            'https://www.boatrace.jp/owpc/pc/race/racelist?hd=20261015&jcd=14&rno=1',
            'https://www.boatrace.jp/owpc/pc/race/racelist?hd=20261016&jcd=02&rno=1',
            'https://www.boatrace.jp/owpc/pc/race/racelist?hd=20261016&jcd=14&rno=1&rno=2',
            'https://www.boatrace.jp/owpc/pc/race/beforeinfo?hd=20261016&jcd=14&rno=1',
            'https://www.boatrace.jp.evil.invalid/owpc/pc/race/racelist?hd=20261016&jcd=14&rno=1',
        ):
            card['source']=invalid
            self.sources();check()
        card['source']=base
        correct=before['source']
        before['source']=correct.replace('rno=1','rno=2')
        self.sources();check()
        before['source']=correct
        for change in ({'race_key':'20261016-14-02'},
                       {'meta':{**self.race['meta'],'date':'2026-10-15'}},
                       {'meta':{**self.race['meta'],'venue_code':'02'}},
                       {'meta':{**self.race['meta'],'race_no':2}}):
            old={k:self.race.get(k) for k in change}
            self.race.update(change)
            self.sources();check()
            self.race.update(old)
        self.sources()
        self.assertIsNotNone(gate.valid(
            self.root,KEY,gate.expected_deadline(KEY,'08:35'),AT))

    def test_official_html_sha_and_symlink_required_before_receipt(self):
        """A SHA declaration is not evidence without exact raw originals."""
        for role in ('racelist','beforeinfo'):
            p=self.root/f'data/raw/20261016/14_01_{role}.html'
            original=p.read_bytes()
            p.write_bytes(original+b' modified')
            self.assertEqual(gate.run(self.root,AT)['created'],[])
            self.assertFalse((self.root/gate.OUT/f'{KEY}.json').exists())
            p.write_bytes(original)
            p.unlink()
            p.symlink_to(self.root/'data/formal_status.json')
            self.assertEqual(gate.run(self.root,AT)['created'],[])
            p.unlink();p.write_bytes(original)
        self.assertEqual(gate.run(self.root,AT)['created'],[KEY])

    def test_scratch_source_identity_and_exact_raw_sha_required(self):
        """An apparently good withdrawal check from another source is unknown.

        Positive eligibility cannot be based on stale/foreign scratch flags
        even when all three source JSON files exist and timestamps are fresh.
        """
        def reject():
            self.sources()
            self.assertIsNone(gate.valid(
                self.root,KEY,gate.expected_deadline(KEY,'08:35'),AT))
            self.assertFalse((self.root/gate.OUT/f'{KEY}.json').exists())
        self.assertIsNotNone(gate.valid(
            self.root,KEY,gate.expected_deadline(KEY,'08:35'),AT))
        for field,invalid in (
            ('schema_version','fake-scratch-v1'),
            ('source_date','20261015'),
            ('race_key','20261016-14-02'),
            ('race_card_sha256','a'*64),
            ('beforeinfo_sha256','b'*64),
            ('suspect_lanes',None),
            ('official_raw_flags',None),
        ):
            original=self.scratch[field]
            self.scratch[field]=invalid
            reject()
            self.scratch[field]=original
        self.sources()
        self.assertEqual(gate.run(self.root,AT)['created'],[KEY])
        receipt=json.loads((self.root/gate.OUT/f'{KEY}.json').read_text())
        self.assertEqual(receipt['official_race_card_sha256'],
                         self.scratch['race_card_sha256'])
        self.assertEqual(receipt['official_beforeinfo_sha256'],
                         self.scratch['beforeinfo_sha256'])

    def test_deadline_bounds_fail_closed(self):
        for offset in (10*60+1,119,60,0,-2):
            self.assertEqual(gate.run(self.root,
                AT+timedelta(minutes=7,seconds=-offset))['created'],[])
        self.assertEqual(gate.run(self.root,AT)['created'],[KEY])

    def test_protected_files_and_uncertain_input_no_receipt(self):
        result=put(self.root,f'data/site_results/{KEY}.json',{'result':'MUST_NOT_READ'})
        put(self.root,f'data/formal_predictions/{KEY}.json',{'prediction':'MUST_NOT_READ'})
        result.chmod(0)
        self.assertEqual(gate.run(self.root,AT)['created'],[KEY])
        # Following runs never recreate an existing first observed record.
        self.assertEqual(gate.run(self.root,AT)['created'],[])

    def test_same_v216_owner_and_strict_stage_allowlist(self):
        workflow=(Path(__file__).resolve().parents[1]/
            '.github/workflows/BOAT_EDGE_V216_SOURCE_DIAGNOSTIC.yml').read_text()
        self.assertIn("python3 scripts/boat_edge_01_gate1c_source_ready.py",workflow)
        self.assertIn("data/site_ops_v220/gate1c_source_ready/",workflow)
        self.assertIn("V216_UNEXPECTED_FROZEN_EVIDENCE_FILE_",workflow)
        self.assertIn("git clean -fd -- data/site_ops_v220/gate1c_source_ready/",workflow)
        self.assertIn("if compgen -G 'data/site_ops_v220/gate1c_source_ready/*.json'",workflow)
        self.assertIn("cron: '4,19,34,49 * * * *'",workflow)
        self.assertNotIn("git push --force",workflow)

    def test_formal_guard_and_symlink_source_fail_closed(self):
        p=self.root/'data/formal_status.json'
        obj=json.loads(p.read_text())
        obj['guards']['results_seen']=True
        put(self.root,'data/formal_status.json',obj)
        with self.assertRaisesRegex(ValueError,'FORMAL_FRESH'):
            gate.run(self.root,AT)
        obj['guards']['results_seen']=False
        put(self.root,'data/formal_status.json',obj)
        fake=put(self.root,'forbidden.json',self.race)
        race=self.root/f'data/races/{KEY}.json'
        race.unlink()
        race.symlink_to(fake)
        self.assertEqual(gate.run(self.root,AT)['created'],[])

if __name__=='__main__':
    unittest.main()
