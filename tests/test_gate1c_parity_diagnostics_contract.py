"""Synthetic-only contract for sampled parity diagnostics; no result access."""
from pathlib import Path
import unittest

SOURCE = Path(__file__).resolve().parents[1] / "scripts/boat_edge_v220_site_ops.py"

class Gate1CParityDiagnosticsContract(unittest.TestCase):
    def test_parity_diagnostic_fields_and_fail_closed_verdict_remain(self):
        text = SOURCE.read_text(encoding="utf-8")
        self.assertIn("'source_ready_prediction_input_parity_diagnostics':[]", text)
        self.assertIn("'race_key':key, 'reason':parity", text)
        self.assertIn("'prediction_saved_at':snap.get('saved_at')", text)
        self.assertIn("'source_ready_observed_at':rec.get('observed_at')", text)
        self.assertIn("'acceptance_99_percent_proven':False", text)
        self.assertIn("'independently_source_eligible_denominator':None", text)

if __name__ == "__main__":
    unittest.main()
