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
    def test_workflow_collector_fallback_is_fail_closed(self):
        workflow = (Path(__file__).resolve().parents[1] / '.github/workflows/capture-pre-result-evidence.yml').read_text()
        self.assertIn("workflow_run:", workflow)
        self.assertIn("workflows: ['BOAT EDGE 自動更新']", workflow)
        self.assertIn("types: [completed]", workflow)
        self.assertIn("github.event.workflow_run.conclusion == 'success'", workflow)
        self.assertIn("github.event.workflow_run.head_branch == 'main'", workflow)
        self.assertIn("github.event.workflow_run.head_repository.full_name == github.repository", workflow)
        self.assertIn("group: official-prerace-evidence", workflow)

    def test_early_morning_t12_schedule_coverage(self):
        workflow = (Path(__file__).resolve().parents[1] / '.github/workflows/capture-pre-result-evidence.yml').read_text()
        self.assertIn("cron: '*/5 22-23 * * *'", workflow)
        self.assertIn("cron: '*/5 0-14 * * *'", workflow)
        # A 08:20 JST race can enter the collector's 3-22 minute window
        # when the schedule wakes at 08:00 or 08:10 JST.
        morning = dt.datetime(2026,10,25,8,10,tzinfo=JST)
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)/"20261025-04-01.json"
            p.write_text(json.dumps(race("20261025-04-01", "08:20")))
            self.assertIsNotNone(eligible(p, morning))

    def test_five_minute_cadence_has_two_nominal_t12_opportunities(self):
        # Deadline at :22 gives eligible scheduled attempts at :05 and :10,
        # before the :10 T-12 cutoff; real schedule execution is not guaranteed.
        deadline = dt.datetime(2026, 10, 25, 8, 22, tzinfo=JST)
        wake_times = [dt.datetime(2026, 10, 25, 8, m, tzinfo=JST) for m in range(0, 25, 5)]
        valid = [wake for wake in wake_times if 12 <= (deadline - wake).total_seconds() / 60 <= 22]
        self.assertGreaterEqual(len(valid), 2)

    def test_workflow_only_captures_and_publishes_from_main(self):
        workflow = (Path(__file__).resolve().parents[1] / '.github/workflows/capture-pre-result-evidence.yml').read_text()
        self.assertEqual(workflow.count("if: github.event_name != 'push' && github.ref == 'refs/heads/main'"), 3)
        self.assertIn("if: always() && github.event_name != 'push'", workflow)

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
            self.assertEqual(result["selection_diagnostic"]["today_race_files"], 5)
            self.assertEqual(result["selection_diagnostic"]["eligible_window_races"], 1)
            self.assertEqual(result["selection_diagnostic"]["excluded_window_or_safety"], 4)

    def test_capacity_prioritizes_t12_eligible_races(self):
        # A delayed scheduled wake must not spend every slot on races
        # already inside T-12 while fresh proof opportunities remain.
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            races = root / "races"
            races.mkdir()
            for i in range(1, 7):
                deadline = "10:40" if i <= 3 else "10:52"
                item = race(f"20261025-04-{i:02d}", deadline)
                (races / (item["race_key"] + ".json")).write_text(json.dumps(item))
            calls = []
            def failing_capture(item, output):
                calls.append(item["race_key"])
                raise ValueError("not_html_document")
            result = batch(races, root / "raw", now=NOW, maximum=3,
                           capture=failing_capture)
            self.assertEqual(calls, [f"20261025-04-{i:02d}" for i in range(4, 7)])
            self.assertEqual(result["selection_diagnostic"]["capacity_not_attempted"], 3)

    def test_early_placeholder_window_is_excluded(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"20261025-04-01.json"
            path.write_text(json.dumps(race("20261025-04-01","11:05")))
            self.assertIsNone(eligible(path,NOW))

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
            self.assertEqual(len(report["t12_receipts"]), 1)
            self.assertTrue(report["t12_receipts"][0]["timestamp_cutoff_ok"])
            self.assertFalse(report["t12_receipts"][0]["exhibition_six_boats_verified"])
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

    def test_placeholder_then_second_attempt_preserves_first(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            races=root/"races"
            races.mkdir()
            item=race("20261025-04-01","10:52")
            item["racers"]=[{"lane": i, "registration_no":str(4000+i)} for i in range(1,7)]
            (races/"20261025-04-01.json").write_text(json.dumps(item))
            blank=b"<html><body>not yet published</body></html>"
            valid=("<html><table><tr><th>コース</th><th>並び</th><th>ST</th></tr>"+
                   "".join(f"<tr><td>{i}</td><td>{i}</td><td>.12</td></tr>" for i in range(1,7))+
                   "</table></html>").encode()
            def capture(item, output, attempt=1):
                output=Path(output)
                output.mkdir(exist_ok=True)
                suffix="" if attempt==1 else f".attempt{attempt}"
                name=item["race_key"]+suffix+".beforeinfo"
                raw=blank if attempt==1 else valid
                (output/(name+".html")).write_bytes(raw)
                audit={"race_key":item["race_key"],"kind":"official_beforeinfo_html",
                    "status":"ok","source":"https://www.boatrace.jp/owpc/pc/race/beforeinfo?hd=20261025&jcd=04&rno=1",
                    "fetched_at":"2026-10-25T10:34:00+09:00","sha256":hashlib.sha256(raw).hexdigest(),
                    "bytes":len(raw)}
                (output/(name+".audit.json")).write_text(json.dumps(audit))
                return audit
            first=batch(races,root/"raw",now=NOW,capture=capture,enriched_output=root/"enriched")
            self.assertEqual(len(first["enriched"]),1,first)
            self.assertEqual(first["enriched"][0]["attempt"],2)
            self.assertEqual(len(first["t12_receipts"]),2)
            for receipt in first["t12_receipts"]:
                self.assertEqual(receipt["deadline_jst"], "2026-10-25T10:52:00+09:00")
                self.assertTrue(receipt["fetched_at"].endswith("+09:00"))
                self.assertRegex(receipt["source_sha256"], r"^[0-9a-f]{64}$")
            self.assertTrue(all(not x["exhibition_six_boats_verified"] for x in first["t12_receipts"]))
            self.assertEqual([x["attempt"] for x in first["captured"]],[1,2])
            original=(root/"raw"/"20261025-04-01.beforeinfo.html").read_bytes()
            self.assertEqual(original,blank)
            second=batch(races,root/"raw",now=NOW,capture=capture,enriched_output=root/"enriched")
            self.assertEqual(second["captured"],[])
            self.assertEqual(second["enriched"],[])
            self.assertEqual((root/"raw"/"20261025-04-01.beforeinfo.html").read_bytes(),original)
            third=batch(races,root/"raw",now=NOW,capture=capture,enriched_output=root/"enriched")
            self.assertEqual(third["captured"],[])

    def test_invalid_audit_never_triggers_retry(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            races=root/"races"
            races.mkdir()
            item=race("20261025-04-01","10:52")
            (races/"20261025-04-01.json").write_text(json.dumps(item))
            rawdir=root/"raw"
            rawdir.mkdir()
            name="20261025-04-01.beforeinfo"
            raw=b"<html><body>pending</body></html>"
            (rawdir/(name+".html")).write_bytes(raw)
            audit={"race_key":item["race_key"],"kind":"official_beforeinfo_html",
                "status":"ok","source":"https://www.boatrace.jp/owpc/pc/race/beforeinfo?hd=20261025&jcd=04&rno=1",
                "fetched_at":"2026-10-25T10:34:00+09:00","sha256":"0"*64,"bytes":len(raw)}
            (rawdir/(name+".audit.json")).write_text(json.dumps(audit))
            calls=[]
            def capture(item,output,attempt=1):
                calls.append(attempt)
                raise AssertionError("capture must not be called on bad audit")
            result=batch(races,rawdir,now=NOW,capture=capture,enriched_output=root/"enriched")
            self.assertEqual(calls,[])
            self.assertTrue(any(x["reason"]=="verification_failed" for x in result["failed"]))
            self.assertFalse((rawdir/"20261025-04-01.attempt2.beforeinfo.html").exists())

    def test_capture_failure_uses_allowlisted_code_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            races=root/"races"
            races.mkdir()
            item=race("20261025-04-01","10:52")
            (races/(item["race_key"]+".json")).write_text(json.dumps(item))
            def known(item, output):
                raise ValueError("redirect_not_allowed")
            report=batch(races,root/"raw",now=NOW,capture=known)
            self.assertEqual(report["failed"][0]["capture_error_code"],"redirect_not_allowed")
            def unknown(item, output):
                raise ValueError("secret response body")
            report=batch(races,root/"raw",now=NOW,capture=unknown)
            self.assertEqual(report["failed"][0]["capture_error_code"],"unclassified")
            self.assertNotIn("secret",json.dumps(report))

    def test_no_data_no_capture(self):
        with tempfile.TemporaryDirectory() as tmp:
            report = batch(tmp, Path(tmp) / "captures", now=NOW)
            self.assertEqual(report["checked"], 0)
            self.assertEqual(report["captured"], [])
            self.assertEqual(report["selection_diagnostic"]["today_race_files"], 0)
            self.assertFalse(report["selection_diagnostic"]["zero_eligible_is_success"])


if __name__ == "__main__":
    unittest.main()
