"""V313 Git/raw HTML attestation tests with synthetic local repository."""
import hashlib
import os
import pathlib
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "scripts"))
from boat_edge_v313_official_raw_attest import official_url_matches, verify_race


def fixture(raw):
    sha = hashlib.sha256(raw).hexdigest()
    return {
        "race_key": "20261013-02-09",
        "meta": {"deadline": "14:48"},
        "source_audit": {
            kind: {
                "status": "ok",
                "source": "https://www.boatrace.jp/owpc/pc/race/" + endpoint +
                          "?hd=20261013&jcd=02&rno=9",
                "sha256": sha,
                "fetched_at": "2026-10-13T14:30:00+09:00",
            } for kind, endpoint in
            (("race_card", "racelist"), ("beforeinfo", "beforeinfo"))
        }
    }


class V313RawAttestation(unittest.TestCase):
    def test_official_race_identity(self):
        url = "https://www.boatrace.jp/owpc/pc/race/racelist?hd=20261013&jcd=02&rno=9"
        self.assertTrue(official_url_matches(url, "race_card", "20261013", "02", 9))
        self.assertFalse(official_url_matches(url.replace("jcd=02", "jcd=03"),
                                             "race_card", "20261013", "02", 9))
        self.assertFalse(official_url_matches(url.replace("www.boatrace.jp", "www.boatrace.jp.attacker.invalid"),
                                             "race_card", "20261013", "02", 9))

    def test_git_predeadline_raw_matches_without_authentication_claim(self):
        raw = b"<html>synthetic official fixture, NOT real site</html>"
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            folder = root / "data" / "raw" / "20261013"
            folder.mkdir(parents=True)
            for kind in ("racelist", "beforeinfo"):
                (folder / ("02_09_" + kind + ".html")).write_bytes(raw)
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            subprocess.run(["git", "add", "data/raw"], cwd=root, check=True)
            env = dict(os.environ, GIT_AUTHOR_DATE="2026-10-13T14:31:00+09:00",
                       GIT_COMMITTER_DATE="2026-10-13T14:31:00+09:00")
            subprocess.run(["git", "-c", "user.name=test", "-c", "user.email=test@example.invalid",
                            "commit", "-q", "-m", "fixture"], cwd=root, env=env, check=True)
            record = fixture(raw)
            report = verify_race(root, record)
            self.assertTrue(report["official"]["race_card"]["evidence_bundle_consistent"])
            self.assertTrue(report["official"]["beforeinfo"]["evidence_bundle_consistent"])
            self.assertFalse(report["github_server_received_before_deadline"])
            self.assertFalse(report["site_source_independently_authenticated"])
            self.assertFalse(report["actual_course_verified"])
            self.assertFalse(report["results_read"])
            (folder / "02_09_beforeinfo.html").write_bytes(b"tampered")
            report = verify_race(root, record)
            self.assertFalse(report["official"]["beforeinfo"]["raw_sha256_matches_audit"])
            self.assertFalse(report["official"]["beforeinfo"]["evidence_bundle_consistent"])

    def test_no_git_provenance_means_not_consistent(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            folder = root / "data" / "raw" / "20261013"
            folder.mkdir(parents=True)
            (folder / "02_09_racelist.html").write_bytes(b"x")
            report = verify_race(root, fixture(b"x"))
            self.assertFalse(report["official"]["race_card"]["local_git_commit_record_predeadline"])
            self.assertFalse(report["official"]["race_card"]["evidence_bundle_consistent"])


if __name__ == "__main__":
    unittest.main()
