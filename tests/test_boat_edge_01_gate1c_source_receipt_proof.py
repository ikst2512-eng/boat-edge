"""Actual local-Git first-add fixtures for conservative 1C source readiness."""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import boat_edge_v220_site_ops as monitor

KEY='20261016-14-01'
DAY='20261016'
AT=datetime(2026,10,16,8,28,tzinfo=timezone(timedelta(hours=9)))
DUE=datetime(2026,10,16,8,35,tzinfo=AT.tzinfo)
SHA='a'*64

def write(root,rel,body):
    path=root/rel
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(body,ensure_ascii=False,sort_keys=True)+'\n',encoding='utf8')
    return hashlib.sha256(path.read_bytes()).hexdigest()

class SourceFirstGitProof(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.git('init','--initial-branch=main')
        self.git('config','user.name','Fixture')
        self.git('config','user.email','fixture@example.test')
        src={}
        for label,base in (('race','data/races'),('odds','data/site_odds'),
                           ('scratch','data/site_scratches_v182')):
            src[label]=write(self.root,f'{base}/{KEY}.json',{'race_key':KEY,'label':label})
        self.receipt={
            'schema':'BOAT_EDGE_GATE1C_PROSPECTIVE_SOURCE_READY_V1',
            'scope':'SITE_PRE_RESULT_SOURCE_OBSERVATION_NO_FORMAL_OR_RESULTS',
            'race_key':KEY,'deadline_jst':'08:35',
            'deadline_at':DUE.astimezone(timezone.utc).isoformat(),
            'observed_at':AT.astimezone(timezone.utc).isoformat(),
            'source_sha256':src,'official_race_card_sha256':SHA,
            'official_beforeinfo_sha256':SHA,
            'official_odds_combinations':120,'six_boat_exhibition_complete':True,
            'first_git_source_commit_independently_proven':False,
            'independently_eligible_denominator_established':False,
            'results_seen':False,'formal_fresh_unlock':False,'scoring':False}
        self.receipt_path=f'data/site_ops_v220/gate1c_source_ready/{KEY}.json'
        write(self.root,self.receipt_path,self.receipt)
        self.git('add','-A')
        self.commit()
    def git(self,*args,env=None):
        e={**os.environ,**(env or {})}
        p=subprocess.run(['git',*args],cwd=self.root,env=e,text=True,
                         capture_output=True,timeout=12)
        self.assertEqual(p.returncode,0,(args,p.stderr))
        return p.stdout.strip()
    def commit(self,time='2026-10-16T08:29:00+09:00'):
        self.git('commit','-m','first pre-result receipt',
                 env={'GIT_COMMITTER_DATE':time,'GIT_AUTHOR_DATE':time})
    def proof(self):
        return monitor.gate1c_source_receipt_first_git_proof(self.root,KEY,self.receipt)
    def test_first_git_tree_shas_and_prospective_time_pass(self):
        code,commit=self.proof()
        self.assertEqual(code,'PASS')
        self.assertEqual(len(commit),40)
        rows=monitor.gate1c_source_receipt_summary(
            self.root,DAY,DUE+timedelta(minutes=10),lambda *_:('PASS','commit'))
        self.assertEqual(rows['source_ready_first_git_proven'],1)
        self.assertEqual(rows['source_ready_without_proven_prediction'],1)
        self.assertEqual(rows['source_ready_missing_prediction_keys'],[KEY])
        self.assertIsNone(rows['independently_source_eligible_denominator'])
        self.assertIsNone(rows['eligible_save_rate_percent'])
        self.assertFalse(rows['acceptance_99_percent_proven'])
        pending=monitor.gate1c_source_receipt_summary(self.root,DAY,AT)
        self.assertEqual(pending['receipts_seen'],1)
        self.assertEqual(pending['receipts_matured'],0)
        self.assertEqual(pending['source_ready_first_git_proven'],0)
        write(self.root,f'data/site_results/{KEY}.json',{'settled':'DO_NOT_OPEN'})
        write(self.root,f'data/formal_predictions/{KEY}.json',{'formal':'DO_NOT_OPEN'})
        self.assertEqual(self.proof()[0],'PASS')
        # Verified prediction must have an existing snapshot AND independent
        # original proof: even a mocked PASS alone cannot fabricate one.
        write(self.root,f'data/site_prediction_snapshots/{KEY}.json',{
            'race_key':KEY,'deadline':'08:35','saved_at':'2026-10-16T08:30:00+09:00'})
        write(self.root,f'data/site_prediction_audit/{KEY}.json',{'pass':True})
        good=monitor.gate1c_source_receipt_summary(
            self.root,DAY,DUE+timedelta(minutes=10),lambda *_:('PASS','commit'))
        self.assertEqual(good['source_ready_with_proven_prediction'],1)
        self.assertEqual(good['source_ready_without_proven_prediction'],0)
        # Independently valid first Git snapshot != proven same source.
        self.assertEqual(good['source_ready_with_exact_race_odds_sha'],0)
        self.assertEqual(good['source_ready_prediction_input_parity_unverified'],1)
        self.assertEqual(good['source_ready_prediction_input_parity_reasons'],
                         {'prediction_race_or_odds_source_sha_mismatch':1})
        self.assertIsNone(good['eligible_save_rate_percent'])
        # A matching race/odds pair with observation BEFORE prediction earns
        # the separate strict parity count, but still NEVER a 99% rate.
        snap={'race_key':KEY,'deadline':'08:35',
              'saved_at':'2026-10-16T08:30:00+09:00',
              'race_sha256':self.receipt['source_sha256']['race'],
              'odds_sha256':self.receipt['source_sha256']['odds']}
        write(self.root,f'data/site_prediction_snapshots/{KEY}.json',snap)
        matching=monitor.gate1c_source_receipt_summary(
            self.root,DAY,DUE+timedelta(minutes=10),lambda *_:('PASS','commit'))
        self.assertEqual(matching['source_ready_with_exact_race_odds_sha'],1)
        self.assertEqual(matching['source_ready_prediction_input_parity_unverified'],0)
        self.assertIsNone(matching['independently_source_eligible_denominator'])
        self.assertFalse(matching['acceptance_99_percent_proven'])
        snap['odds_sha256']='f'*64
        write(self.root,f'data/site_prediction_snapshots/{KEY}.json',snap)
        mismatched=monitor.gate1c_source_receipt_summary(
            self.root,DAY,DUE+timedelta(minutes=10),lambda *_:('PASS','commit'))
        self.assertEqual(mismatched['source_ready_with_exact_race_odds_sha'],0)
        self.assertEqual(mismatched['source_ready_prediction_input_parity_reasons'],
                         {'prediction_race_or_odds_source_sha_mismatch':1})
        snap['odds_sha256']=self.receipt['source_sha256']['odds']
        snap['saved_at']='2026-10-16T08:27:00+09:00'
        write(self.root,f'data/site_prediction_snapshots/{KEY}.json',snap)
        observed_later=monitor.gate1c_source_receipt_summary(
            self.root,DAY,DUE+timedelta(minutes=10),lambda *_:('PASS','commit'))
        self.assertEqual(observed_later['source_ready_with_exact_race_odds_sha'],0)
        self.assertEqual(observed_later['source_ready_prediction_input_parity_reasons'],
                         {'source_ready_observation_after_prediction':1})

    def test_changed_first_receipt_bytes_or_source_tree_rejected(self):
        self.receipt['official_odds_combinations']=121
        write(self.root,self.receipt_path,self.receipt)
        self.assertEqual(self.proof()[0],'receipt_metadata_or_window_unverified')
        self.receipt['official_odds_combinations']=120
        write(self.root,self.receipt_path,self.receipt)
        self.receipt['source_sha256']['odds']='f'*64
        write(self.root,self.receipt_path,self.receipt)
        self.assertEqual(self.proof()[0],'receipt_changed_after_first_git_add')

    def test_missing_source_at_original_commit_rejected(self):
        self.receipt['source_sha256']['race']='b'*64
        write(self.root,self.receipt_path,self.receipt)
        self.git('add','-A')
        self.git('commit','-m','later malicious change')
        self.assertEqual(self.proof()[0],'receipt_changed_after_first_git_add')

    def test_postdeadline_commit_and_ambiguous_readd_refused(self):
        self.git('rm',self.receipt_path)
        self.git('commit','-m','remove')
        write(self.root,self.receipt_path,self.receipt)
        self.git('add','-A')
        self.git('commit','-m','recreate')
        self.assertEqual(self.proof()[0],'receipt_first_git_add_missing_or_ambiguous')

    def test_late_git_first_add_fails_even_with_valid_observation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            # Copy only an already-safe tracked receipt into a fresh test repo.
            subprocess.run(['git','init','-q',str(root)],check=True)
            subprocess.run(['git','config','user.name','Fixture'],cwd=root,check=True)
            subprocess.run(['git','config','user.email','fixture@example.test'],cwd=root,check=True)
            for base in ('data/races','data/site_scratches_v182','data/site_odds'):
                folder=root/base
                folder.mkdir(parents=True,exist_ok=True)
                (folder/f'{KEY}.json').write_bytes(
                    (self.root/base/f'{KEY}.json').read_bytes())
            p=root/self.receipt_path;p.parent.mkdir(parents=True,exist_ok=True)
            p.write_bytes((self.root/self.receipt_path).read_bytes())
            env={**os.environ,'GIT_AUTHOR_DATE':'2026-10-16T08:34:00+09:00',
                 'GIT_COMMITTER_DATE':'2026-10-16T08:34:00+09:00'}
            subprocess.run(['git','add','-A'],cwd=root,check=True)
            subprocess.run(['git','commit','-qm','late backfilled receipt'],
                           cwd=root,env=env,check=True)
            self.assertEqual(monitor.gate1c_source_receipt_first_git_proof(
                root,KEY,self.receipt)[0],'receipt_first_git_add_outside_window')

if __name__=='__main__':
    unittest.main()
