import sys
import subprocess
import unittest
from pathlib import Path


class ImportProbe(unittest.TestCase):
    def test_missing_ocp_has_actionable_error_without_gui_side_effects(self):
        code = """
import importlib.abc
import sys

class BlockOCP(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname == "OCP" or fullname.startswith("OCP."):
            raise ImportError("OCP hidden by test")
        return None

sys.meta_path.insert(0, BlockOCP())
try:
    import zencad
except ImportError as exception:
    assert "python -m pip install zencad" in str(exception)
else:
    raise AssertionError("zencad import unexpectedly succeeded")

assert "PyQt5" not in sys.modules
assert "zenframe" not in sys.modules
"""
        result = subprocess.run(
            [sys.executable, "-c", code],
            cwd=Path(__file__).parents[1],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "")

    def test_headless_import_needs_neither_legacy_occ_nor_qt(self):
        code = """
import importlib.abc
import sys

blocked = ("OCC", "PyQt5")

class BlockLegacyAndQt(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if any(fullname == name or fullname.startswith(name + ".") for name in blocked):
            raise ImportError("blocked import: " + fullname)
        return None

sys.meta_path.insert(0, BlockLegacyAndQt())
import zencad
assert abs(zencad.box(1).unlazy().mass() - 1.0) < 1e-8
"""
        result = subprocess.run(
            [sys.executable, "-c", code],
            cwd=Path(__file__).parents[1],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_local_assembly_is_lazy_and_has_no_termin_dependency(self):
        code = """
import sys
import zencad

assert "zencad.assemble" not in sys.modules
module = zencad.assemble
assert module is sys.modules["zencad.assemble"]
assert "termin" not in sys.modules
"""
        result = subprocess.run(
            [sys.executable, "-c", code],
            cwd=Path(__file__).parents[1],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
