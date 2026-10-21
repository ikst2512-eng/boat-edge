import hashlib
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from boat_edge_naruto_offline_capture_replay import inspect_capture

HTML = ("<table><tr><th>艇</th><th>一周</th><th>まわり足</th><th>直線</th></tr>"
        + "".join(f"<tr><td>{i}号艇</td><td>36.2</td><td>5.7</td><td>7.0</td></tr>"
                  for i in range(1, 7)) + "</table>").encode()
SHA = hashlib.sha256(HTML).hexdigest()
PARAMS = dict(race_key="20261021-14-12",
              source_url="https://www.n14.jp/example/source",
              captured_at="2026-10-21T14:00:00+09:00",
              deadline="2026-10-21T14:15:00+09:00",
              expected_sha256=SHA)


class CaptureReplayTests(unittest.TestCase):
    def check(self, **replace):
        args = dict(PARAMS)
        args.update(replace)
        return inspect_capture(HTML, **args)

    def test_without_race_proof_refused(self):
        self.assertEqual(self.check()["status"], "RACE_IDENTITY_UNVERIFIED")

    def test_explicit_proof_can_parse(self):
        self.assertEqual(self.check(independent_race_proof=True)["status"],
                         "COMPLETE_SIX_BOATS")

    def test_sha_mismatch(self):
        self.assertEqual(self.check(expected_sha256="0" * 64)["status"],
                         "SHA256_MISMATCH")

    def test_wrong_day(self):
        self.assertEqual(self.check(captured_at="2026-10-20T14:00:00+09:00")["status"],
                         "RECEIPT_RACE_DATE_MISMATCH")

    def test_after_deadline(self):
        self.assertEqual(self.check(captured_at=PARAMS["deadline"])["status"],
                         "INVALID_OR_LATE_RECEIPT")

    def test_nonofficial_domain(self):
        self.assertEqual(self.check(source_url="https://example.org/")["status"],
                         "UNTRUSTED_SOURCE_URL")

    def test_malformed_port(self):
        self.assertEqual(self.check(source_url="https://www.n14.jp:bad/path")["status"],
                         "UNTRUSTED_SOURCE_URL")

    def test_wrong_venue(self):
        self.assertEqual(self.check(race_key="20261021-06-12")["status"],
                         "INVALID_RACE_KEY")


if __name__ == "__main__":
    unittest.main()
