"""Synthetic only; no network, existing results or formal cohort reads."""
import hashlib
import importlib.util
import tempfile
import unittest
from datetime import date,timedelta
from pathlib import Path

SRC=Path(__file__).resolve().parent.parent/"scripts/boat_edge_02_five_year_archive_gate.py"
spec=importlib.util.spec_from_file_location("history_gate",SRC)
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

def digest(content):
    return hashlib.sha256(content).hexdigest()

class ArchiveAudit(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.archive=self.root/"external-license-archives"
        self.archive.mkdir()
        self.grant=self.root/"grant.txt"
        self.grant.write_bytes(b"fictional test grant; no actual permission")
        self.manifest={"schema":mod.SCHEMA,"rights":{
            "review_status":"HUMAN_REVIEWED_APPROVED",
            "automated_download":False,"third_party_scraping":False,
            "local_archival_storage":True,"offline_statistical_analysis":True,
            "ml_training":True,"provider":"FAKE_FIXTURE_ONLY",
            "rightsholder":"FAKE_FIXTURE_ONLY","grant_reference":"FAKE:testing",
            "reviewer":"FAKE","reviewed_at":date.today().isoformat(),
            "grant_sha256":digest(self.grant.read_bytes()),
            "expires_on":(date.today()+timedelta(days=15)).isoformat(),
            "scope_years":[2021,2022,2023,2024,2025],
            "data_kinds":sorted(mod.KINDS)},"partitions":[]}
        for month in sorted(mod.MONTHS):
            for kind in sorted(mod.KINDS):
                name=f"{month}_{kind}.fixture"
                data=f"fixture only {name}".encode()
                (self.archive/name).write_bytes(data)
                self.manifest["partitions"].append({
                    "month":month,"kind":kind,"file":name,
                    "declared_record_count":1,"size_bytes":len(data),"sha256":digest(data)})
    def run_audit(self):
        return mod.audit(self.manifest,self.archive,self.grant,repo_root=self.root)
    def test_120_partitions_only_inventory(self):
        output=self.run_audit()
        self.assertEqual(output["verified_local_file_count"],120)
        self.assertFalse(output["permission_independently_verified"])
        self.assertFalse(output["unseen_holdout_accuracy_proven"])
    def test_missing_month(self):
        self.manifest["partitions"].pop()
        with self.assertRaisesRegex(ValueError,"MONTHLY_120_PARTITIONS"):
            self.run_audit()
    def test_tampered_bytes(self):
        (self.archive/self.manifest["partitions"][0]["file"]).write_bytes(b"tampered")
        with self.assertRaisesRegex(ValueError,"BYTE_INTEGRITY_FAILURE"):
            self.run_audit()
    def test_no_permission(self):
        self.manifest["rights"]["ml_training"]=False
        with self.assertRaisesRegex(ValueError,"RIGHTS_SCOPE_MISSING"):
            self.run_audit()
        self.manifest["rights"]["ml_training"]=True
        self.manifest["rights"]["expires_on"]="2020-01-01"
        with self.assertRaisesRegex(ValueError,"GRANT_EXPIRED"):
            self.run_audit()
    def test_traversal(self):
        self.manifest["partitions"][0]["file"]="../grant.txt"
        with self.assertRaisesRegex(ValueError,"BAD_ARCHIVE_PATH"):
            self.run_audit()
    def test_no_repo_formal_data(self):
        protected=self.root/"data"
        protected.mkdir()
        with self.assertRaisesRegex(ValueError,"PROTECTED_REPOSITORY_DATA_FORBIDDEN"):
            mod.audit(self.manifest,protected,self.grant,repo_root=self.root)

if __name__=="__main__":
    unittest.main()
