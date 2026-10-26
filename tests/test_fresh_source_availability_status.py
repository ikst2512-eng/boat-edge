"""Check PRE_RESULT CSV publication diagnostics without accessing results."""
import ast
from pathlib import Path
import textwrap
import unittest

WORKFLOW = Path(".github/workflows/auto-update.yml")


def source_availability(fetched):
    source = WORKFLOW.read_text(encoding="utf-8")
    start = source.index('          status["source_availability"]={')
    end = source.index('          preview_roles=', start)
    script = textwrap.dedent(source[start:end])
    namespace = {"status": {}, "fetched": fetched}
    exec(compile(ast.parse(script), "<source-availability>", "exec"), namespace)
    return namespace["status"]["source_availability"]


class SourceAvailabilityStatus(unittest.TestCase):
    def test_partial_predeadline_rows_are_not_available(self):
        result = source_availability({
            "original_exhibition": {
                "rows": [{"レースコード": "future"}], "error": None,
                "retry_count": 2, "predeadline_race_rows_missing": 5,
            },
            "race_cards": {
                "rows": [{"レースコード": "future"}], "error": None,
                "retry_count": 0, "predeadline_race_rows_missing": 0,
            },
        })
        self.assertEqual(result["original_exhibition"]["state"], "PARTIAL_PENDING")
        self.assertEqual(result["original_exhibition"]["missing_pending_races"], 5)
        self.assertEqual(result["race_cards"]["state"], "AVAILABLE")

    def test_errors_and_unpublished_take_priority(self):
        for error, rows, expected in [
            ("not_published", [], "NOT_PUBLISHED"),
            ("timeout", [], "FETCH_ERROR"),
            (None, [], "EMPTY_RESPONSE"),
        ]:
            with self.subTest(error=error):
                result = source_availability({
                    "stt": {"rows": rows, "error": error, "retry_count": 1,
                            "predeadline_race_rows_missing": 3}})
                self.assertEqual(result["stt"]["state"], expected)


if __name__ == "__main__":
    unittest.main()
