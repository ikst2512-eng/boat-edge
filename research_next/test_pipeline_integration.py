"""Offline end-to-end acquisition audit: no network, no results data."""
import hashlib
import tempfile
import unittest
from datetime import datetime,timedelta,timezone
from pathlib import Path
from unittest.mock import MagicMock
from scheduled_probe import run
from probe_availability import run_probe
from probe_report import report
from probe_health import assess

JST=timezone(timedelta(hours=9))
BASE="https://boatracecsv.github.io/data/programs/"

class PipelineIntegrationTests(unittest.TestCase):
    def test_schedule_to_proven_race_without_results(self):
        now=datetime(2026,10,23,12,0,tzinfo=JST)
        day=now.strftime("%Y%m%d")
        race=day+"1201"
        deadline=now+timedelta(minutes=40)
        path=f"{day[:4]}/{day[4:6]}/{day[6:]}.csv"
        title_url=BASE+"title/"+path
        cards_url=BASE+"race_cards/"+path
        title=f"レースコード,電話投票締切予定\n{race},{deadline:%H:%M}\n".encode()
        cards=("レースコード,"+",".join(f"艇{i}_全国勝率" for i in range(1,7))+f"\n{race},6,6,6,6,6,6\n").encode()
        requests=[]
        def opener(request,timeout=12):
            url=request.full_url
            requests.append(url)
            if url not in (title_url,cards_url):
                raise AssertionError("unexpected source")
            resp=MagicMock()
            resp.status=200
            resp.geturl.return_value=url
            resp.read.return_value=title if url==title_url else cards
            resp.__enter__.return_value=resp
            return resp
        def probe(code,deadline_jst,source_url,root):
            return run_probe(code,deadline_jst,source_url,root,
                             clock=lambda:now,opener=opener)
        with tempfile.TemporaryDirectory() as d:
            status=run(now,root=d,opener=opener,probe=probe,capture_clock=lambda:now)
            summary=report(d)
            self.assertEqual(status["due"],1)
            self.assertEqual(status["captured"],1)
            self.assertEqual(status["failed"],0)
            self.assertEqual(summary["title_sources"],1)
            self.assertEqual(summary["manifests"],1)
            self.assertEqual(summary["unique_races_12"],1)
            self.assertEqual(summary["invalid"],0)
            self.assertEqual(summary["invalid_title_sources"],0)
            verdict=assess(dict(status,status="ok"),summary)
            self.assertEqual(verdict["proven_captures"],1)
            self.assertEqual(requests,[title_url,cards_url])
            self.assertEqual(len(list(Path(d).rglob("*.body"))),2)

if __name__=="__main__":
    unittest.main()
