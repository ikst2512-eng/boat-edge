#!/usr/bin/env python3
"""No-network tests for the optional Naruto original-exhibition parser."""
import sys
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from boat_edge_naruto_original_exhibition_parser import parse_naruto_original_exhibition

JST = timezone(timedelta(hours=9))
NOW = datetime(2026, 10, 21, 14, 0, tzinfo=JST)
DUE = NOW + timedelta(minutes=15)


def fixture(duplicate=False, missing=False):
    header = "<tr><th>艇</th><th>一周</th><th>まわり足</th><th>直線</th></tr>"
    rows = "".join(
        f"<tr><td>{i}号艇</td><td>{'─' if missing and i == 6 else '36.50'}</td>"
        f"<td>5.70</td><td>7.05</td></tr>" for i in range(1, 7))
    table = "<table>" + header + rows + "</table>"
    return table * (2 if duplicate else 1)


class TestNarutoParser(unittest.TestCase):
    def test_six_boat_complete(self):
        r = parse_naruto_original_exhibition(fixture(), identity_verified=True,
                                               fetched_at=NOW, deadline=DUE)
        self.assertEqual(r["status"], "COMPLETE_SIX_BOATS")
        self.assertEqual(r["boats"]["1"]["lap"], 36.5)

    def test_identity_missing(self):
        self.assertEqual(parse_naruto_original_exhibition(fixture(),
                         fetched_at=NOW, deadline=DUE)["status"], "RACE_IDENTITY_UNVERIFIED")

    def test_timestamp_missing(self):
        self.assertEqual(parse_naruto_original_exhibition(fixture(),
                         identity_verified=True)["status"], "INVALID_TIMESTAMPS")

    def test_no_header(self):
        self.assertEqual(parse_naruto_original_exhibition("<table><tr><td>展示</td></tr></table>",
                         identity_verified=True, fetched_at=NOW, deadline=DUE)["status"],
                         "TABLE_NOT_FOUND_OR_AMBIGUOUS")

    def test_ambiguous_tables(self):
        self.assertEqual(parse_naruto_original_exhibition(fixture(duplicate=True),
                         identity_verified=True, fetched_at=NOW, deadline=DUE)["status"],
                         "TABLE_NOT_FOUND_OR_AMBIGUOUS")

    def test_unmeasured(self):
        self.assertEqual(parse_naruto_original_exhibition(fixture(missing=True),
                         identity_verified=True, fetched_at=NOW, deadline=DUE)["status"],
                         "NOT_MEASURED_OR_NOT_YET_PUBLISHED")

    def test_nested_table_does_not_duplicate_rows(self):
        wrapped = "<table><tr><td>" + fixture() + "</td></tr></table>"
        out = parse_naruto_original_exhibition(wrapped, identity_verified=True,
                                               fetched_at=NOW, deadline=DUE)
        self.assertEqual(out["status"], "COMPLETE_SIX_BOATS")

    def test_bad_input_type(self):
        out = parse_naruto_original_exhibition({"not": "html"}, identity_verified=True,
                                               fetched_at=NOW, deadline=DUE)
        self.assertEqual(out["status"], "PARSE_FAILED")

    def test_unlabelled_table_rejected(self):
        html = fixture().replace("<th>艇</th>", "<th>名前</th>")
        self.assertEqual(parse_naruto_original_exhibition(html, identity_verified=True,
                         fetched_at=NOW, deadline=DUE)["status"], "TABLE_NOT_FOUND_OR_AMBIGUOUS")

    def test_truncated_boat_row_rejected(self):
        html = fixture() + ""
        html = html.replace("<td>6号艇</td><td>36.50</td><td>5.70</td><td>7.05</td>",
                            "<td>6号艇</td><td>36.50</td>")
        self.assertNotEqual(parse_naruto_original_exhibition(html, identity_verified=True,
                            fetched_at=NOW, deadline=DUE)["status"], "COMPLETE_SIX_BOATS")

    def test_common_official_header_aliases(self):
        html = (fixture().replace("一周</th>", "1周タイム</th>")
                .replace("まわり足</th>", "回り足タイム</th>")
                .replace("直線</th>", "直線タイム</th>"))
        self.assertEqual(parse_naruto_original_exhibition(html, identity_verified=True,
                         fetched_at=NOW, deadline=DUE)["status"], "COMPLETE_SIX_BOATS")

    def test_deadline(self):
        self.assertEqual(parse_naruto_original_exhibition(fixture(),
                         identity_verified=True, fetched_at=DUE, deadline=DUE)["status"],
                         "STALE_AFTER_DEADLINE")


if __name__ == "__main__":
    unittest.main()
