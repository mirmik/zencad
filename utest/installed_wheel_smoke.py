"""Smoke the installed wheel from a directory outside the source checkout."""

import importlib.metadata
import os
from pathlib import Path
import shutil
import subprocess
import sys
from tempfile import TemporaryDirectory

from evalcache.dircache_v2 import DirCache_v2
from zencad.runtime import RunnerMessage, RunnerSupervisor
import zencad
from zencad import _typed as typed
from zencad.convert.api import _from_brep, _to_brep, _to_stl


def main():
    assert RunnerMessage is not None
    assert RunnerSupervisor is not None
    assert zencad.__version__ == importlib.metadata.version("zencad")
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

        typed_runtime = typed.Runtime.deferred(cache=False)
        curve = typed_runtime.circle(2)
        curve2 = typed_runtime.segment2(
            typed_runtime.point2(0, 0),
            typed_runtime.point2(3, 0),
        ).trim(0.5, 2.5)
        assert type(curve) is typed.Curve
        assert curve.point(0).value() == (2.0, 0.0, 0.0)
        assert type(curve2) is typed.Curve2
        assert curve2.point(0.5).value() == (0.5, 0.0)
        surface = typed_runtime.cylinder_surface(2)
        sweep_surface = typed_runtime.sweep_surface(
            typed_runtime.circle(1),
            typed_runtime.circle(3),
        )
        assert type(surface) is typed.Surface
        assert surface.point(0, 3).value() == (2.0, 0.0, 3.0)
        assert type(sweep_surface) is typed.Surface
        assert len(sweep_surface.native().Bounds()) == 4

        script_path = temporary_path / "headless_model.py"
        script_path.write_text(
            "import sys\n"
            "from zencad import box, display, show\n"
            "display(box(1))\n"
            "show()\n"
            "assert 'PyQt5' not in sys.modules\n"
            "assert 'zenframe' not in sys.modules\n",
            encoding="utf-8",
        )
        subprocess.run(
            [sys.executable, "-m", "zencad", "--no-show", str(script_path)],
            cwd=temporary_path,
            check=True,
        )
        console_script = shutil.which("zencad")
        assert console_script is not None
        subprocess.run(
            [console_script, "--no-show", str(script_path)],
            cwd=temporary_path,
            check=True,
        )

    print("Installed wheel geometry/I/O smoke: OK")


if __name__ == "__main__":
    main()
