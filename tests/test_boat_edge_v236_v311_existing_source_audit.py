"""V311 synthetic-only tests for actual-entry provenance and deadline audit."""
import pathlib
import sys
import tempfile
import json
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "scripts"))
from boat_edge_v311_existing_source_audit import audit_directory, audit_race


def fixture():
    return {
        "race_key": "20261013-02-09",
        "meta": {"deadline": "14:48"},
        "source_audit": {
            "race_card": {"status": "ok", "source": "https://www.boatrace.jp/race",
                          "sha256": "a" * 64, "fetched_at": "2026-10-13T14:30:00+09:00"},
            "beforeinfo": {"status": "ok", "source": "https://www.boatrace.jp/before",
                           "sha256": "b" * 64, "fetched_at": "2026-10-13T14:40:00+09:00"},
            "original_exhibition": {"status": "ok", "source": "https://boatracecsv.github.io/something.csv",
                                    "sha256": "c" * 64, "fetched_at": "2026-10-13T14:42:00+09:00"},
        },
        "beforeinfo": {"start_exhibition": [
            {"lane": i, "course": i, "st": "0.10"} for i in range(1, 7)
        ]},
        "actual_entry": [{"lane": i, "course": i, "exhibition_st": 0.10} for i in range(1, 7)],
        "validation": {"result": "NEVER_READ"},
    }


class V311ExistingAudit(unittest.TestCase):
    def test_good_metadata_does_not_prove_actual_course(self):
        row = audit_race(fixture())
        self.assertTrue(row["source_metadata"]["beforeinfo"]["pre_deadline_metadata_qualified"])
        self.assertTrue(row["start_exhibition_course_permutation_recorded"])
        self.assertEqual(row["entry_semantics"], "START_EXHIBITION_NOT_ACTUAL_ENTRY")
        self.assertFalse(row["actual_course_independently_verified"])
        self.assertFalse(row["ready_for_v308_actual_course_research"])
        self.assertFalse(row["boaters_verified"])
        self.assertFalse(row["kyoteibiyori_verified"])
        self.assertFalse(row["results_accessed"])

    def test_after_deadline_and_missing_source_rejected(self):
        row = fixture()
        row["source_audit"]["beforeinfo"]["fetched_at"] = "2026-10-13T14:49:00+09:00"
        report = audit_race(row)
        self.assertFalse(report["source_metadata"]["beforeinfo"]["pre_deadline_metadata_qualified"])
        self.assertIn("BEFOREINFO_NOT_PREDEADLINE_PROVEN", report["reasons"])
        row["source_audit"]["beforeinfo"]["fetched_at"] = None
        self.assertFalse(audit_race(row)["source_metadata"]["beforeinfo"]["fetched_before_deadline"])

    def test_entry_relabel_and_directory_summary(self):
        row = fixture()
        row["beforeinfo"]["start_exhibition"] = [{"lane": 1, "course": 1}]
        self.assertFalse(audit_race(row)["start_exhibition_course_permutation_recorded"])
        with tempfile.TemporaryDirectory() as root:
            directory = pathlib.Path(root)
            (directory / "good.json").write_text(json.dumps(fixture()), encoding="utf-8")
            (directory / "bad.json").write_text("broken", encoding="utf-8")
            output = audit_directory(directory)
            self.assertEqual(output["inspected"], 1)
            self.assertEqual(output["invalid"], 1)
            self.assertEqual(output["ready_for_v308"], 0)

    def test_fails_on_bad_key(self):
        row = fixture()
        row["race_key"] = "20261013-99-20"
        with self.assertRaises(ValueError):
            audit_race(row)


if __name__ == "__main__":
    unittest.main()
