"""V298: Old UI installer timers must not compete with current site/AI owners."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parent.parent


class LegacyUiOwnerTests(unittest.TestCase):
    def test_legacy_ui_installers_manual_only(self):
        for name in ("site-v106.yml", "site-v108.yml"):
            with self.subTest(name=name):
                file = ROOT / ".github" / "workflows" / name
                text = file.read_text(encoding="utf-8")
                head = text.split("\npermissions:", 1)[0]
                self.assertIn("\non:\n", head)
                self.assertIn("\n  workflow_dispatch:", head)
                for forbidden in ("\n  push:", "\n  schedule:", "\n  workflow_run:", "\n  pull_request:", "cron:"):
                    self.assertNotIn(forbidden, head, (name, forbidden))
                # Keep explicit operator recovery possible, but prohibit automated writes.
                self.assertIn("contents: write", text)
                self.assertIn("V298: Legacy UI installer is manual recovery ONLY.", head)

    def test_current_collectors_and_v235_not_retired(self):
        active = {
            "auto-update.yml": "BOAT EDGE 自動更新",
            "V235.yml": "BOAT EDGE V235",
        }
        for name, expected in active.items():
            with self.subTest(name=name):
                text = (ROOT / ".github" / "workflows" / name).read_text(encoding="utf-8")
                head = text.split("\npermissions:", 1)[0]
                self.assertIn(expected, head)
                self.assertIn("\n  schedule:", head)
                self.assertIn("cron:", head)


if __name__ == "__main__":
    unittest.main()
