"""Execute the V344 JavaScript fixture under the existing Development CI test discovery.
CI checks out tests/ and assets/ but intentionally not data/races/.
"""
import pathlib
import subprocess
import unittest


class V344OriginalExhibitionNodeTest(unittest.TestCase):
    def test_original_exhibition_fixture(self):
        root = pathlib.Path(__file__).resolve().parents[1]
        result = subprocess.run(
            ["node", "--test", "tests/v344_original_exhibition_fixture.test.cjs"],
            cwd=root, capture_output=True, text=True, timeout=40, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + "\n" + result.stderr)


if __name__ == "__main__":
    unittest.main()
