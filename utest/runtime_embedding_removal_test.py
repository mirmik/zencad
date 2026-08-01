from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest


ROOT = Path(__file__).parents[1]
ACTIVE_RUNTIME_FILES = (
    ROOT / "zencad/__main__.py",
    ROOT / "zencad/showapi.py",
    ROOT / "zencad/gui/actions.py",
    ROOT / "zencad/gui/display.py",
    ROOT / "zencad/gui/mainwindow.py",
)
FORBIDDEN_RUNTIME_TEXT = (
    "zenframe.unbound",
    "unbound_frame_summon",
    "unbound_worker",
    "QWindow.fromWinId",
    "createWindowContainer",
    "managed_runtime",
)


class RuntimeEmbeddingRemovalTest(unittest.TestCase):
    def test_active_runtime_has_no_foreign_window_path(self):
        for path in ACTIVE_RUNTIME_FILES:
            source = path.read_text(encoding="utf-8")
            for forbidden in FORBIDDEN_RUNTIME_TEXT:
                self.assertNotIn(forbidden, source, f"{forbidden} remains in {path}")
        self.assertFalse((ROOT / "zencad/gui/display_unbounded.py").exists())

    def test_removed_process_modes_fail_with_migration_hint(self):
        for option in ("--unbound", "--frame", "--sleeped"):
            result = subprocess.run(
                [sys.executable, "-m", "zencad", option],
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Foreign-window", result.stdout)
            self.assertIn("--display", result.stdout)

    def test_no_show_remains_a_qt_free_same_process_mode(self):
        with TemporaryDirectory() as directory:
            script = Path(directory) / "model.py"
            script.write_text(
                "import sys\n"
                "assert 'PyQt5' not in sys.modules\n"
                "from zencad import box, display, show\n"
                "display(box(1))\n"
                "show()\n"
                "assert 'PyQt5' not in sys.modules\n"
                "assert 'zenframe' not in sys.modules\n",
                encoding="utf-8",
            )
            subprocess.run(
                [sys.executable, "-m", "zencad", "--no-show", str(script)],
                cwd=ROOT,
                check=True,
            )


if __name__ == "__main__":
    unittest.main()
