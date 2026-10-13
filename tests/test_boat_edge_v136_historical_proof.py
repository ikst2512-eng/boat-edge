#!/usr/bin/env python3
"""V136: synthetic Git first-add and race-scoped audit proofs, no result APIs."""
import copy
from datetime import datetime, timedelta
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

from scripts.site_v136_historical_proof import check_historical_proof

KEY = "20261008-14-01"
SNAP = f"data/site_prediction_snapshots/{KEY}.json"
AUDIT = f"data/site_prediction_audit/{KEY}.json"
ORIGINAL_TIME = "2026-10-08T08:29:00+09:00"


def write_json(root, path, val):
    p = root / path
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(val, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    return p


class HistoricalV125Proof(unittest.TestCase):
    def prepare(self, *, commit_time=ORIGINAL_TIME, snap_time="2026-10-08T08:28:30+09:00"):
        tmp = tempfile.TemporaryDirectory()
        root = Path(tmp.name)
        snapshot = {
            "race_key": KEY,
            "deadline": "08:35",
            "schema_version": "boat-edge-server-site-final-v123",
            "snapshot_window": "FINAL_15M",
            "prediction_kind": "SITE_REFERENCE_V122",
            "first_saved_at": snap_time,
            "saved_at": snap_time,
            "guards": {"results_seen": False, "unlock": False, "scoring": False},
        }
        path = write_json(root, SNAP, snapshot)
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        audit = {
            "schema_version": "boat-edge-final15m-audit-v125",
            "race_key": KEY, "pass": True,
            "latest_snapshot_sha256": digest,
            "latest_snapshot_saved_at": snapshot["saved_at"],
            "revisions": [{
                "snapshot_sha256": digest,
                "saved_at": snapshot["saved_at"],
                "first_saved_at": snapshot["first_saved_at"],
                "prediction_kind": snapshot["prediction_kind"],
                "intrinsic_flags": {"schema_v123": True, "pre_result_guards": True},
            }],
        }
        write_json(root, AUDIT, audit)
        subprocess.run(["git", "init", "-q"], cwd=root, check=True)
        subprocess.run(["git", "config", "user.name", "Fixture"], cwd=root, check=True)
        subprocess.run(["git", "config", "user.email", "fixture@example.invalid"], cwd=root, check=True)
        subprocess.run(["git", "add", SNAP, AUDIT], cwd=root, check=True)
        env = os.environ.copy()
        env["GIT_AUTHOR_DATE"] = commit_time
        env["GIT_COMMITTER_DATE"] = commit_time
        subprocess.run(["git", "commit", "-qm", "original prospective SITE snapshot"],
                       cwd=root, check=True, env=env)
        return tmp, root, snapshot

    def test_real_first_git_predeadline_and_matching_historical_receipt(self):
        tmp, root, snapshot = self.prepare()
        try:
            decision, sha = check_historical_proof(root, KEY, snapshot)
            self.assertEqual(decision, "PASS")
            self.assertRegex(sha, r"^[0-9a-f]{40}$")
        finally:
            tmp.cleanup()

    def test_today_only_index_is_not_a_historical_gate(self):
        tmp, root, snapshot = self.prepare()
        try:
            write_json(root, "data/site_prediction_audit/index.json",
                       {"date": "20261015", "audited": {}})
            self.assertEqual(check_historical_proof(root, KEY, snapshot)[0], "PASS")
        finally:
            tmp.cleanup()

    def test_invented_sidecar_cannot_replace_original_snapshot(self):
        tmp, root, snapshot = self.prepare()
        try:
            # A later replacement of the same path is NOT the originally fixed pick.
            changed = copy.deepcopy(snapshot)
            changed["other_prediction"] = "1-2-3"
            p = write_json(root, SNAP, changed)
            digest = hashlib.sha256(p.read_bytes()).hexdigest()
            audit = json.loads((root / AUDIT).read_text())
            audit["latest_snapshot_sha256"] = digest
            audit["revisions"][0]["snapshot_sha256"] = digest
            write_json(root, AUDIT, audit)
            self.assertEqual(check_historical_proof(root, KEY, snapshot)[0],
                             "first_git_snapshot_bytes_mismatch")
        finally:
            tmp.cleanup()

    def test_git_commit_after_deadline_rejected(self):
        tmp, root, snapshot = self.prepare(commit_time="2026-10-08T08:36:00+09:00")
        try:
            self.assertEqual(check_historical_proof(root, KEY, snapshot)[0],
                             "first_git_commit_not_predeadline")
        finally:
            tmp.cleanup()

    def test_earlier_than_claimed_first_snapshot_commit_rejected(self):
        tmp, root, snapshot = self.prepare(commit_time="2026-10-08T08:25:00+09:00")
        try:
            self.assertEqual(check_historical_proof(root, KEY, snapshot)[0],
                             "first_git_commit_before_snapshot")
        finally:
            tmp.cleanup()

    def test_historical_audit_absent_rejected(self):
        tmp, root, snapshot = self.prepare()
        try:
            (root / AUDIT).unlink()
            self.assertEqual(check_historical_proof(root, KEY, snapshot)[0],
                             "historical_v125_or_snapshot_missing")
        finally:
            tmp.cleanup()

    def test_audit_revision_bad_guards_rejected(self):
        tmp, root, snapshot = self.prepare()
        try:
            audit = json.loads((root / AUDIT).read_text())
            audit["revisions"][0]["intrinsic_flags"]["pre_result_guards"] = False
            write_json(root, AUDIT, audit)
            self.assertEqual(check_historical_proof(root, KEY, snapshot)[0],
                             "historical_v125_intrinsic_unverified")
        finally:
            tmp.cleanup()

    def test_history_race_identity_rejected(self):
        tmp, root, snapshot = self.prepare()
        try:
            wrong = dict(snapshot, race_key="20261014-14-02")
            self.assertEqual(check_historical_proof(root, KEY, wrong)[0],
                             "history_race_identity_mismatch")
        finally:
            tmp.cleanup()

    def test_v136_legacy_installer_cannot_overwrite_first_git_scoring(self):
        workflow = (Path(__file__).resolve().parents[1]
                    / ".github/workflows/site-v136.yml").read_text(encoding="utf-8")
        self.assertIn("    if: false", workflow)
        self.assertIn("github.event_name == 'workflow_dispatch'", workflow)
        self.assertIn("    needs: [install]", workflow)
        scorer = (Path(__file__).resolve().parents[1]
                  / "scripts/site_accuracy_v136.py").read_text(encoding="utf-8")
        self.assertIn("check_historical_proof(BASE,key,snap)", scorer)
        self.assertNotIn('audited.get(key)', scorer)

    def test_result_never_needed_and_no_formal_read(self):
        tmp, root, snapshot = self.prepare()
        try:
            # No result, payout or formal_status file exists in the fixture.
            self.assertEqual(check_historical_proof(root, KEY, snapshot)[0], "PASS")
        finally:
            tmp.cleanup()


if __name__ == "__main__":
    unittest.main()
