"""Synthetic-only tests for read-only race-code joining."""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

SRC = Path(__file__).resolve().parents[1] / "scripts" / "fresh_race_csv_state_compare.py"
spec = importlib.util.spec_from_file_location("compare", SRC)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

class Response:
    status = 200
    def __init__(self, body): self.body = body
    def __enter__(self): return self
    def __exit__(self, *args): return False
    def read(self): return self.body

class Tests(unittest.TestCase):
    def test_join_and_false_formal_claim(self):
        key = "20261026-21-02"
        data = ("レースコード,値\n202610262101,x\n202610262102,y\n").encode()
        state = {"race_key": key, "source_audit": {"stt": {"status": "missing", "sha256": "other"}}}
        with patch.object(mod.Path, "is_file", return_value=True), \
             patch.object(mod.Path, "read_text", return_value=json.dumps(state)):
            record = mod.compare(key, opener=lambda *a, **k: Response(data))
        self.assertEqual(record["sources"]["stt"]["matching_rows"], 1)
        self.assertEqual(record["sources"]["stt"]["match_kind"], "ONE")
        self.assertFalse(record["sources"]["stt"]["same_bytes_as_saved_audit"])
        self.assertFalse(record["formal_eligible"])
        self.assertIsNotNone(record["sources"]["stt"]["fetch_started_at_jst"])
        self.assertIsNotNone(record["sources"]["stt"]["fetch_completed_at_jst"])
        self.assertIsNotNone(record["sources"]["stt"]["parse_completed_at_jst"])
        self.assertIsNotNone(record["sources"]["stt"]["observed_before_deadline_at_fetch"])
        self.assertFalse(record["sources"]["race_cards"]["sha_comparison_applicable"])
        self.assertIsNone(record["sources"]["race_cards"]["same_bytes_as_saved_audit"])
        self.assertTrue(record["sources"]["stt"]["sha_comparison_applicable"])
    def test_invalid_key(self):
        with self.assertRaises(ValueError): mod.compare("../unsafe")

if __name__ == "__main__":
    unittest.main()
