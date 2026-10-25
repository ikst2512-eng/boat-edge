"""Offline tests of bounded scheduled PRE_RESULT capture selection."""
import datetime as dt
import json
import hashlib
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from capture_imminent_pre_result import batch, eligible
from archive_pre_result_source import JST

NOW = dt.datetime(2026, 10, 25, 10, 35, tzinfo=JST)


def race(key, deadline, locked=True):
    day, venue, no = key.split("-")
    return {"race_key": key, "meta": {
        "date": "2026-10-25", "venue_code": venue, "race_no": int(no),
        "deadline": deadline, "phase": "PRE_RESULT" if locked else "RESULT",
        "results_seen": False if locked else True, "scoring": False,
        "unlock": False}}


class BatchTests(unittest.TestCase):
    def test_only_imminent_locked_races_are_captured(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp) / "races"
            directory.mkdir()
            cases = [
                race("20261025-04-01", "10:52"),
                race("20261025-04-02", "10:34"),
                race("20261025-04-03", "12:20"),
                race("20261025-04-04", "10:50", locked=False),
                race("20261025-04-05", "10:36"),
            ]
            for item in cases:
                (directory / (item["race_key"] + ".json")).write_text(json.dumps(item))
            calls = []
            def fake_capture(item, output):
                calls.append(item["race_key"])
                return {"sha256": "a" * 64}
            result = batch(directory, Path(tmp) / "captures", now=NOW, capture=fake_capture)
            self.assertEqual(calls, ["20261025-04-01"])
            self.assertEqual(len(result["captured"]), 1)

    def test_mismatched_filename_is_skipped(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "20261025-04-02.json"
            p.write_text(json.dumps(race("20261025-04-01", "10:52")))
            self.assertIsNone(eligible(p, NOW))

    def test_verified_html_produces_separate_enriched_artifact(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            races = root / "races"
            races.mkdir()
            item = race("20261025-04-01", "10:52")
            item["racers"] = [{"lane": i, "registration_no": str(4000+i)} for i in range(1,7)]
            (races / "20261025-04-01.json").write_text(json.dumps(item))
            html = ("<html><table><tr><th>コース</th><th>並び</th><th>ST</th></tr>"
                    + "".join(f"<tr><td>{i}</td><td>{[2,1,3,4,5,6][i-1]}</td><td>.12</td></tr>" for i in range(1,7))
                    + "</table></html>").encode()
            def capture(item, directory):
                directory = Path(directory)
                directory.mkdir(parents=True, exist_ok=True)
                (directory / (item["race_key"] + ".beforeinfo.html")).write_bytes(html)
                audit = {"race_key":item["race_key"],"kind":"official_beforeinfo_html","status":"ok",
                         "source":"https://www.boatrace.jp/owpc/pc/race/beforeinfo?hd=20261025&jcd=04&rno=1",
                         "fetched_at":"2026-10-25T10:34:00+09:00",
                         "sha256":hashlib.sha256(html).hexdigest(),"bytes":len(html)}
                (directory / (item["race_key"] + ".beforeinfo.audit.json")).write_text(json.dumps(audit))
                return audit
            report = batch(races, root / "raw", now=NOW, capture=capture, enriched_output=root / "enriched")
            self.assertEqual(len(report["enriched"]), 1, report)
            enriched = json.loads((root / "enriched" / "20261025-04-01.json").read_text())
            self.assertEqual(enriched["actual_entry"], [2,1,3,4,5,6])
            self.assertNotIn("actual_entry", json.loads((races / "20261025-04-01.json").read_text()))

    def test_one_failed_race_does_not_block_other_capture(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            races=root/"races"
            races.mkdir()
            for key,deadline in (("20261025-04-01","10:48"),("20261025-04-02","10:52")):
                (races/(key+".json")).write_text(json.dumps(race(key,deadline)))
            def fake_capture(item,output):
                if item["race_key"].endswith("-01"):
                    raise OSError("simulated network error")
                return {"sha256":"a"*64}
            result=batch(races,root/"capture",now=NOW,capture=fake_capture)
            self.assertEqual(len(result["failed"]),1)
            self.assertEqual([r["key"] for r in result["captured"]],["20261025-04-02"])

    def test_no_data_no_capture(self):
        with tempfile.TemporaryDirectory() as tmp:
            report = batch(tmp, Path(tmp) / "captures", now=NOW)
            self.assertEqual(report["checked"], 0)
            self.assertEqual(report["captured"], [])


if __name__ == "__main__":
    unittest.main()
