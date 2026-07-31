"""Smoke the installed wheel from a directory outside the source checkout."""

import importlib.metadata
import os
from pathlib import Path
from tempfile import TemporaryDirectory

from evalcache.dircache_v2 import DirCache_v2
import zencad
from zencad.convert.api import _from_brep, _to_brep, _to_stl


def main():
    checkout = os.environ.get("GITHUB_WORKSPACE")
    if checkout:
        package_path = Path(zencad.__file__).resolve()
        assert not package_path.is_relative_to(Path(checkout).resolve())

    installed = {
        distribution.metadata["Name"].lower()
        for distribution in importlib.metadata.distributions()
    }
    assert not installed.intersection({"vtk", "pyqt5", "zenframe", "termin"})

    with TemporaryDirectory() as temporary_directory:
        temporary_path = Path(temporary_directory)
        zencad.lazy.cache = DirCache_v2(str(temporary_path / "cache"))

        shape = zencad.box(20, center=True) - zencad.sphere(5)
        expected_mass = shape.unlazy().mass()
        brep_path = temporary_path / "smoke.brep"
        stl_path = temporary_path / "smoke.stl"

        _to_brep(shape.unlazy(), str(brep_path))
        restored = _from_brep(str(brep_path))
        assert abs(restored.mass() - expected_mass) < 1e-8
        assert _to_stl(shape.unlazy(), str(stl_path), 0.1)
        assert stl_path.stat().st_size > 0

    print("Installed wheel geometry/I/O smoke: OK")


if __name__ == "__main__":
    main()
