"""Protect the read-only Fresh upstream publication classification."""
from pathlib import Path
import unittest

SRC = Path(__file__).resolve().parents[1] / "scripts" / "fresh_csv_http_diagnostic.py"

class FreshHTTPContract(unittest.TestCase):
    def test_publication_classes_and_headers(self):
        s = SRC.read_text(encoding="utf-8")
        for label in ("published_with_rows", "published_empty", "not_published_http_404", "http_or_transport_error"):
            self.assertIn(label, s)
        self.assertIn('entry["csv_headers"] = list(reader.fieldnames or [])', s)
        self.assertIn('entry["race_code_rows"] = sum(bool(str(', s)
        self.assertIn('"formal_unlock_authorized": False', s)
        self.assertIn('"results_accessed": False', s)

if __name__ == "__main__":
    unittest.main()
