"""V125 must not erase V229 immutable source provenance in the same race audit.

Fixture-only: never read repository race outcomes, formal results or network.
"""
from datetime import datetime, timedelta, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import textwrap
import unittest

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "site-v125.yml"
JST = timezone(timedelta(hours=9))


def run_audit(root):
    text = WORKFLOW.read_text(encoding="utf-8")
    start = 'cat > "$RUNNER_TEMP/v125_audit_once.py" <<\'PY\''
    assert text.count(start) == 1, "V125_REPLAY_SCRIPT_NOT_UNIQUE"
    body = text.split(start, 1)[1].split("\n          PY", 1)[0]
    source = textwrap.dedent(body)
    return subprocess.run(
        [sys.executable, "-c", source], cwd=root,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        check=False,
    )


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8")
    return hashlib.sha256(path.read_bytes()).hexdigest()


class V229AtomicProvenancePreservation(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.key = datetime.now(JST).strftime("%Y%m%d") + "-09-09"
        self.snapshot = self.root / "data/site_prediction_snapshots" / (self.key + ".json")
        self.audit = self.root / "data/site_prediction_audit" / (self.key + ".json")
        self.reference = "data/site_autopilot/v229_evidence/" + self.key + ".json"
        self.proof = "b" * 64
        self.original = {
            "schema_version": "boat-edge-server-site-final-v123",
            "race_key": self.key,
            "snapshot_window": "FINAL_15M",
            "prediction_kind": "SITE_REFERENCE_V122",
            "selection_policy": "V122_SCENARIO_AWARE_PROBABILITY_FIRST",
            "minutes_to_deadline": 5,
            "race_sha256": "a" * 64,
            "odds_sha256": None,
            "first_saved_at": "2026-10-15T14:00:00+09:00",
            "saved_at": "2026-10-15T14:00:02+09:00",
            "guards": {"results_seen": False, "unlock": False, "scoring": False},
            "modes": {"hit": {"tickets": [
                {"combo": "1-2-" + str(i), "p": 1.0, "odds": None}
                for i in range(1, 7)
            ]}},
        }
        self.sha = write_json(self.snapshot, self.original)
        write_json(self.root / self.reference,
                   {"schema": "BOAT_EDGE_V229_ATOMIC_PRE_RESULT_SOURCE_EVIDENCE_V1",
                    "race_key": self.key, "snapshot_sha256": self.sha})
        self.old = {
            "schema_version": "boat-edge-final15m-audit-v125",
            "race_key": self.key, "first_audited_at": "2026-10-15T05:00:00+00:00",
            "last_audited_at": "2026-10-15T05:00:00+00:00",
            "latest_snapshot_sha256": self.sha,
            "latest_snapshot_saved_at": self.original["saved_at"],
            "revision_count": 1,
            "revisions": [{"snapshot_sha256": self.sha,
                           "saved_at": self.original["saved_at"],
                           "atomic_pre_result_proof_sha256": self.proof}],
            "pass": True,
            "atomic_pre_result_audit": True,
            "scope": "SITE_ONLY_NOT_FORMAL_FRESH",
            "source_evidence_file": self.reference,
        }
        write_json(self.audit, self.old)

    def test_same_frozen_bytes_keep_original_v229_proof_and_source_path(self):
        result = run_audit(self.root)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        new = json.loads(self.audit.read_text(encoding="utf-8"))
        self.assertTrue(new["pass"])
        self.assertTrue(new["atomic_pre_result_audit"])
        self.assertEqual(new["scope"], "SITE_ONLY_NOT_FORMAL_FRESH")
        self.assertEqual(new["source_evidence_file"], self.reference)
        self.assertEqual(new["latest_snapshot_sha256"], self.sha)
        self.assertEqual(new["revisions"][0]["atomic_pre_result_proof_sha256"], self.proof)
        self.assertFalse((self.root / "data/formal_results").exists())

    def test_changed_snapshot_cannot_inherit_old_atomic_approval(self):
        newer = dict(self.original)
        newer["saved_at"] = "2026-10-15T14:00:03+09:00"
        new_sha = write_json(self.snapshot, newer)
        self.assertNotEqual(self.sha, new_sha)
        result = run_audit(self.root)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        new = json.loads(self.audit.read_text(encoding="utf-8"))
        self.assertEqual(new["latest_snapshot_sha256"], new_sha)
        self.assertNotIn("atomic_pre_result_audit", new)
        self.assertNotIn("source_evidence_file", new)
        original_revision = next(
            item for item in new["revisions"]
            if item["snapshot_sha256"] == self.sha
        )
        self.assertEqual(original_revision["atomic_pre_result_proof_sha256"], self.proof)
        fresh_revision = next(
            item for item in new["revisions"]
            if item["snapshot_sha256"] == new_sha
        )
        self.assertNotIn("atomic_pre_result_proof_sha256", fresh_revision)

    def test_unproven_marker_does_not_acquire_atomic_proof(self):
        old = dict(self.old)
        old.pop("atomic_pre_result_audit")
        write_json(self.audit, old)
        result = run_audit(self.root)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        new = json.loads(self.audit.read_text(encoding="utf-8"))
        self.assertNotIn("atomic_pre_result_audit", new)


if __name__ == "__main__":
    unittest.main()
