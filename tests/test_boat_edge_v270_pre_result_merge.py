#!/usr/bin/env python3
"""Offline regression of the actual PRE_RESULT Git publish shell.
Never accesses result endpoints, external network, or formal target history.
"""
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
YAML=(ROOT/'.github/workflows/auto-update.yml').read_text(encoding='utf-8')

def shell():
    tail=YAML.split('      - name: 更新内容を保存\n',1)[1].split('        run: |\n',1)[1]
    return '\n'.join(x[10:] if x.startswith('          ') else x for x in tail.splitlines())+'\n'

def run(cmd,cwd=None,input=None,ok=True):
    p=subprocess.run(cmd,cwd=cwd,input=input,text=True,capture_output=True,timeout=40)
    if ok and p.returncode:
        raise AssertionError(f"{cmd}: {p.returncode}\n{p.stdout[-2000:]}\n{p.stderr[-2000:]}")
    return p

def git(where,*args,ok=True):
    return run(['git','-C',str(where),*args],ok=ok)

def put(where,path,body):
    p=where/path
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(body,encoding='utf-8')

class SourceMerge(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        t=Path(self.tmp.name)
        self.remote=t/'remote.git'
        self.writer=t/'writer'
        self.collector=t/'collector'
        run(['git','init','--bare','--initial-branch=main',str(self.remote)])
        run(['git','clone',str(self.remote),str(self.writer)])
        for p in (self.writer,):
            git(p,'config','user.name','Test')
            git(p,'config','user.email','test@example.com')
        self.lock=json.dumps({'guards':{'results_seen':False,'unlock':False,'scoring':False,
                 'RESULT_UNLOCK_TOKEN':None},'formalFirst100':{'races':0}})
        put(self.writer,'data/formal_status.json',self.lock)
        put(self.writer,'data/races/20261012-19-09.json','BASE_RACE\n')
        put(self.writer,'data/raw/20261012/19_09_beforeinfo.html','BASE_BEFORE\n')
        # The production collector now calls V277 before each Git push.
        # Clone the REAL guard script into both offline writers; a missing
        # fixture must never masquerade as correct rebase rejection.
        guard=ROOT/'scripts/boat_edge_v277_snapshot_push_guard.py'
        self.assertTrue(guard.is_file())
        put(self.writer,'scripts/boat_edge_v277_snapshot_push_guard.py',
            guard.read_text(encoding='utf-8'))
        git(self.writer,'add','data','scripts')
        git(self.writer,'commit','-m','base PRE_RESULT only')
        git(self.writer,'push','-u','origin','main')
        run(['git','clone',str(self.remote),str(self.collector)])
        git(self.collector,'config','user.name','Test')
        git(self.collector,'config','user.email','test@example.com')
    def publish_remote(self):
        git(self.writer,'add','data')
        git(self.writer,'commit','-m','other authorized writer')
        git(self.writer,'push','origin','main')
    def execute(self):
        return run(['bash','-e','-o','pipefail'],cwd=self.collector,input=shell(),ok=False)
    def test_shell_parses_and_has_bounded_rebase(self):
        run(['bash','-n'],input=shell())
        for phrase in ('V270_UNSAFE_CONFLICT_FAIL_CLOSED','git checkout --ours',
                       'git rebase --abort','V270_FORMAL_PRE_RESULT_LOCK_PRESERVED',
                       'data/races/20??????-??-??.json'):
            self.assertIn(phrase,shell())
        self.assertNotIn('git push --force',shell())
    def test_preserves_remote_conflict_and_commits_unrelated_source(self):
        put(self.writer,'data/races/20261012-19-09.json','REMOTE_NEW_RACE\n')
        put(self.writer,'data/raw/20261012/19_09_beforeinfo.html','REMOTE_NEW_BEFORE\n')
        self.publish_remote()
        put(self.collector,'data/races/20261012-19-09.json','COLLECTOR_OLDER_RACE\n')
        put(self.collector,'data/raw/20261012/19_09_beforeinfo.html','COLLECTOR_OLDER_BEFORE\n')
        put(self.collector,'data/races/20261012-03-01.json','NEW_DISJOINT_PRE_RESULT\n')
        process=self.execute()
        self.assertEqual(process.returncode,0,process.stdout[-2500:]+process.stderr[-2500:])
        self.assertIn('V270_PRESERVE_PUBLISHED_SOURCE_ON_CONFLICT',process.stdout)
        git(self.collector,'fetch','origin','main')
        def source(path):
            return git(self.collector,'show','origin/main:'+path).stdout.strip()
        self.assertEqual(source('data/races/20261012-19-09.json'),'REMOTE_NEW_RACE')
        self.assertEqual(source('data/raw/20261012/19_09_beforeinfo.html'),'REMOTE_NEW_BEFORE')
        self.assertEqual(source('data/races/20261012-03-01.json'),'NEW_DISJOINT_PRE_RESULT')
        self.assertEqual(json.loads(source('data/formal_status.json'))['guards']['results_seen'],False)
    def test_blocks_source_update_if_remote_race_was_frozen_during_collection(self):
        # Another workflow may freeze an original race AFTER the collector
        # started. Even a disjoint data file must not justify overwriting
        # evidence for that now-immutable race.
        put(self.writer,'data/site_prediction_snapshots/20261012-19-09.json',
            '{"schema":"OFFLINE_FROZEN_PRE_RESULT_FIXTURE"}\\n')
        self.publish_remote()
        put(self.collector,'data/races/20261012-19-09.json',
            'COLLECTOR_STALE_SOURCE_AFTER_FROZEN\\n')
        put(self.collector,'data/races/20261012-03-01.json',
            'NEW_DISJOINT_PRE_RESULT\\n')
        process=self.execute()
        self.assertNotEqual(process.returncode,0,
            'V277 must reject overwrite of newly frozen remote race source')
        self.assertIn('V277_FROZEN_RACE_SOURCE_MUTATION_BLOCKED_20261012-19-09',
            process.stderr)
        self.assertNotIn('V270_PRE_RESULT_SAFE_PUSH_PASS',process.stdout)
        git(self.collector,'fetch','origin','main')
        remote=git(self.collector,'show',
            'origin/main:data/races/20261012-19-09.json').stdout.strip()
        self.assertEqual(remote,'BASE_RACE')
        self.assertNotIn('20261012-03-01',
            git(self.collector,'ls-tree','-r','origin/main').stdout)

    def test_blocks_conflict_in_formal_guard(self):
        put(self.writer,'data/formal_status.json',self.lock[:-1]+', "remote_change":1}')
        self.publish_remote()
        put(self.collector,'data/formal_status.json',self.lock[:-1]+', "collector_change":1}')
        put(self.collector,'data/races/20261012-03-01.json','NEW_DISJOINT_PRE_RESULT\n')
        process=self.execute()
        self.assertNotEqual(process.returncode,0,'Formal provenance conflict must fail closed')
        self.assertIn('V270_UNSAFE_CONFLICT_FAIL_CLOSED data/formal_status.json',process.stdout)
        self.assertNotIn('NEW_DISJOINT_PRE_RESULT',git(self.writer,'ls-tree','-r','HEAD').stdout)

if __name__=='__main__':
    unittest.main()
