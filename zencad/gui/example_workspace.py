"""Disposable editable copies of the bundled ZenCad examples."""

from pathlib import Path
import shutil
import tempfile


class ExampleWorkspace:
    """Copy bundled examples before the editor is allowed to modify them."""

    def __init__(self, source_root):
        self.source_root = Path(source_root).resolve()
        self._temporary_directory = None
        self._copy_root = None

    def prepare(self, source_path):
        source_path = Path(source_path).resolve()
        try:
            relative_path = source_path.relative_to(self.source_root)
        except ValueError as exception:
            raise ValueError(
                "Example path is outside the bundled examples"
            ) from exception
        if not source_path.is_file():
            raise FileNotFoundError(source_path)

        if self._copy_root is None:
            self._temporary_directory = tempfile.TemporaryDirectory(
                prefix="zencad-examples-"
            )
            self._copy_root = (
                Path(self._temporary_directory.name) / "examples"
            )
            try:
                shutil.copytree(
                    self.source_root,
                    self._copy_root,
                    ignore=shutil.ignore_patterns(
                        "__pycache__", "*.pyc", "*.pyo"
                    ),
                )
            except Exception:
                self.cleanup()
                raise
        return self._copy_root / relative_path

    def relative_path(self, path):
        """Return a copied example's relative path, or ``None`` otherwise."""
        if self._copy_root is None:
            return None
        try:
            return Path(path).resolve().relative_to(self._copy_root)
        except ValueError:
            return None

    def cleanup(self):
        if self._temporary_directory is not None:
            self._temporary_directory.cleanup()
        self._temporary_directory = None
        self._copy_root = None
