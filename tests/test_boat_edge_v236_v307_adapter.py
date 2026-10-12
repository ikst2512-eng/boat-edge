"""Synthetic tests for V307 strict pre-result provenance adapter."""
import importlib.util
import pathlib
import unittest

SOURCE = pathlib.Path(__file__).resolve().parents[1] / "scripts/boat_edge_v307_pre_result_adapter.py"
spec = importlib.util.spec_from_file_location("v307_adapter", SOURCE)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def fixture():
    return {
        "race_key": "SYNTHETIC-01",
        "deadline_jst": "2026-10-13T12:00:00+09:00",
        "frozen_at_jst": "2026-10-13T11:50:00+09:00",
        "source_sha256": "a" * 64,
        "source_verified": True,
        "actual_course_by_boat": {"1": 2, "2": 1, "3": 3, "4": 4, "5": 5, "6": 6},
        "strength_by_boat": {str(i): float(i) for i in range(1, 7)}
    }


class V307Adapter(unittest.TestCase):
    def test_maps_boat_to_actual_course(self):
        record = fixture()
        result = m.validated_course_strengths(record)
        self.assertEqual(result[1], 2.0)
        self.assertEqual(result[2], 1.0)
        self.assertEqual(len(m.provenance_digest(record)), 64)

    def test_rejects_unverified_late_or_incomplete(self):
        for key, value in (
            ("source_verified", False),
            ("frozen_at_jst", "2026-10-13T12:00:00+09:00"),
            ("source_sha256", "fake"),
            ("actual_course_by_boat", {"1": 1}),
            ("actual_course_by_boat", {str(i): 1 for i in range(1, 7)}),
            ("strength_by_boat", {str(i): 0 for i in range(1, 7)}),
        ):
            with self.subTest(key=key):
                record = fixture()
                record[key] = value
                with self.assertRaises(ValueError):
                    m.validated_course_strengths(record)

    def test_no_unknown_fields(self):
        record = fixture()
        record["result"] = "1-2-3"
        with self.assertRaises(ValueError):
            m.validated_course_strengths(record)


if __name__ == "__main__":
    unittest.main()
