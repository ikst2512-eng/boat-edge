"""V298: Old UI installer timers must not compete with current site/AI owners."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parent.parent


class LegacyUiOwnerTests(unittest.TestCase):
    def test_legacy_ui_installers_remain_deleted(self):
        # Both V106 and V108 installers were fully retired; allowing their
        # reintroduction would risk rewrites of modern prediction UI assets.
        for name in ("site-v106.yml", "site-v108.yml"):
            with self.subTest(name=name):
                file = ROOT / ".github" / "workflows" / name
                self.assertFalse(file.exists(), "Retired installer must remain absent")

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
