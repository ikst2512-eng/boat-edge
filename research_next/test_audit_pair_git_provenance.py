"""Negative controls: the pre-scoring proof gate must reject absent evidence."""
import importlib.util
import pathlib
import unittest

MODULE = pathlib.Path(__file__).with_name("audit_pair_git_provenance.py")
spec = importlib.util.spec_from_file_location("audit_pair_git_provenance", MODULE)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class PairProvenanceTests(unittest.TestCase):
    def test_empty_manifest_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "RESEARCH_SCOPE_REQUIRED"):
            mod.verify(pathlib.Path("."), {})

    def test_missing_both_frozen_models_fails(self):
        with self.assertRaisesRegex(ValueError, "MISSING_SIDE_baseline"):
            mod.verify(pathlib.Path("."), {
                "scope": "RESEARCH_ONLY_PRE_OUTCOME_PAIR",
                "race_key": "20261025-06-08",
                "deadline_jst": "2026-10-25T14:06:00+09:00",
            })

    def test_no_implicit_utc_self_report(self):
        with self.assertRaisesRegex(ValueError, "JST_TIMESTAMP_REQUIRED"):
            mod.timestamp("2026-10-25T14:06:00+00:00")

    def test_race_key_must_match_day(self):
        with self.assertRaisesRegex(ValueError, "DEADLINE_RACE_MISMATCH"):
            mod.verify(pathlib.Path("."), {
                "scope": "RESEARCH_ONLY_PRE_OUTCOME_PAIR",
                "race_key": "20261025-06-08",
                "deadline_jst": "2026-10-26T14:06:00+09:00",
            })


if __name__ == "__main__":
    unittest.main()
