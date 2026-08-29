from pathlib import Path
import re
import unittest

import zencad


ROOT = Path(__file__).parents[1]


class VersionTest(unittest.TestCase):
    def test_runtime_version_matches_project_metadata(self):
        pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
        match = re.search(
            r'^version\s*=\s*"([^"]+)"\s*$',
            pyproject,
            flags=re.MULTILINE,
        )
        self.assertIsNotNone(match)
        self.assertEqual(zencad.__version__, match.group(1))


if __name__ == "__main__":
    unittest.main()
