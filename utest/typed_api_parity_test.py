from pathlib import Path
import subprocess
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
CHECKER = ROOT / "tools" / "check_typed_api_parity.py"


class TypedApiParityContract(unittest.TestCase):
    def test_legacy_surface_is_classified_and_signature_locked(self):
        result = subprocess.run(
            [sys.executable, str(CHECKER)],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertRegex(
            result.stdout,
            r"typed API parity: \d+ symbols; .*missing=\d+",
        )


if __name__ == "__main__":
    unittest.main()
