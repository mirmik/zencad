from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from zencad.gui.example_workspace import ExampleWorkspace


class ExampleWorkspaceTest(unittest.TestCase):
    def test_copies_the_tree_once_and_keeps_sources_pristine(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            source_root = root / "bundled"
            first = source_root / "group" / "first.py"
            second = source_root / "group" / "second.py"
            asset = source_root / "group" / "image.png"
            cache = source_root / "group" / "__pycache__" / "first.pyc"
            cache.parent.mkdir(parents=True)
            first.write_text("original\n", encoding="utf-8")
            second.write_text("second\n", encoding="utf-8")
            asset.write_bytes(b"image")
            cache.write_bytes(b"cache")

            workspace = ExampleWorkspace(source_root)
            copied_first = workspace.prepare(first)
            copied_first.write_text("edited\n", encoding="utf-8")
            copied_second = workspace.prepare(second)

            self.assertEqual(first.read_text(encoding="utf-8"), "original\n")
            self.assertEqual(
                copied_first.read_text(encoding="utf-8"), "edited\n"
            )
            self.assertEqual(
                copied_second.read_text(encoding="utf-8"), "second\n"
            )
            self.assertEqual(
                copied_second.with_name("image.png").read_bytes(), b"image"
            )
            self.assertFalse(
                copied_first.parent.joinpath("__pycache__").exists()
            )
            self.assertEqual(
                workspace.relative_path(copied_first),
                Path("group/first.py"),
            )
            self.assertIsNone(workspace.relative_path(first))

            copy_root = copied_first.parents[1]
            workspace.cleanup()
            self.assertFalse(copy_root.exists())

    def test_rejects_paths_outside_the_bundled_tree(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            source_root = root / "bundled"
            source_root.mkdir()
            outside = root / "outside.py"
            outside.write_text("pass\n", encoding="utf-8")

            workspace = ExampleWorkspace(source_root)
            with self.assertRaisesRegex(ValueError, "outside"):
                workspace.prepare(outside)


if __name__ == "__main__":
    unittest.main()
