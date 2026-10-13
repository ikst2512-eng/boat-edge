import csv
import io
import sys
import unittest
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from boat_edge_v409_boatracecsv_offline_asof_audit import audit

DAY=date(2026,9,30)
KEY="202609300101"

def csvbytes(fields, values):
    output=io.StringIO()
    w=csv.DictWriter(output,fieldnames=fields,lineterminator="\n")
    w.writeheader()
    for row in values:w.writerow(row)
    return output.getvalue().encode("utf-8-sig")

def cards():
    return csvbytes(["レースコード","レース日","艇1_登録番号"],[
        {"レースコード":KEY,"レース日":DAY.isoformat(),"艇1_登録番号":"4501"}])

def preview(capture="2026-09-30T08:25:00+09:00",deadline="08:35"):
    return csvbytes(["レースコード","レース日","レース場","レース回","締切時刻","取得日時"],[
        {"レースコード":KEY,"レース日":DAY.isoformat(),"レース場":"01",
         "レース回":"01R","締切時刻":deadline,"取得日時":capture}])

class V409Tests(unittest.TestCase):
    def test_valid_preview_timestamp_is_unverified_not_authorized(self):
        a=audit(DAY,{"race_cards":cards(),"stt":preview()})
        self.assertEqual(a["preview_status"]["stt"]["timestamp_eligible_unverified"],1)
        self.assertFalse(a["capture_git_first_commit_verified"])
        self.assertFalse(a["top3_top5_top10_accuracy_measured"])
        self.assertFalse(a["result_or_payout_accessed"])
    def test_after_deadline_rejected(self):
        a=audit(DAY,{"race_cards":cards(),"stt":preview("2026-09-30T08:36:00+09:00")})
        self.assertEqual(a["preview_status"]["stt"]["not_before_deadline"],1)
    def test_wrong_day_capture_rejected(self):
        a=audit(DAY,{"race_cards":cards(),"stt":preview("2026-09-29T08:25:00+09:00")})
        self.assertEqual(a["preview_status"]["stt"]["capture_wrong_day"],1)
    def test_naive_time_rejected(self):
        a=audit(DAY,{"race_cards":cards(),"stt":preview("2026-09-30T08:25:00")})
        self.assertEqual(a["preview_status"]["stt"]["invalid_timestamp"],1)
    def test_duplicate_race_key_rejected(self):
        duplicate=csvbytes(["レースコード","レース日"],[
            {"レースコード":KEY,"レース日":DAY.isoformat()},
            {"レースコード":KEY,"レース日":DAY.isoformat()}])
        with self.assertRaisesRegex(ValueError,"DUPLICATE_SOURCE_RACE_KEY"):
            audit(DAY,{"race_cards":duplicate})
    def test_results_source_forbidden(self):
        with self.assertRaisesRegex(ValueError,"RESULTS_OR_UNKNOWN_SOURCE_FORBIDDEN"):
            audit(DAY,{"race_cards":cards(),"results":b"data"})
    def test_formal_fresh_protected(self):
        with self.assertRaisesRegex(ValueError,"FORMAL_FRESH_OR_OUTSIDE_HISTORICAL_DAY"):
            audit(date(2026,10,1),{"race_cards":cards()})
    def test_preview_race_key_mismatch(self):
        wrong=preview().decode("utf-8-sig").replace(",01,01R,",",02,01R,")
        with self.assertRaisesRegex(ValueError,"PREVIEW_VENUE_OR_RACE_MISMATCH"):
            audit(DAY,{"race_cards":cards(),"stt":wrong.encode()})
    def test_missing_optional_preview_is_explicit(self):
        a=audit(DAY,{"race_cards":cards()})
        self.assertEqual(a["preview_status"]["stt"]["source_not_supplied"],1)
        self.assertEqual(a["race_card_rows"],1)
    def test_four_sources_all_same_race(self):
        a=audit(DAY,{"race_cards":cards(),**{s:preview() for s in
                    ("stt","tkz","sui","original_exhibition")}})
        for s in ("stt","tkz","sui","original_exhibition"):
            self.assertEqual(a["preview_status"][s]["timestamp_eligible_unverified"],1)

if __name__=="__main__":unittest.main()
