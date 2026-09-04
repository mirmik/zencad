"""Import the installed GUI wheel outside the source checkout."""

import importlib
import importlib.metadata
import os
from pathlib import Path
import re
import sys

import zencad


def main():
    assert zencad.__version__ == importlib.metadata.version("zencad")
    checkout = os.environ.get("GITHUB_WORKSPACE")
    if checkout:
        package_path = Path(zencad.__file__).resolve()
        assert not package_path.is_relative_to(Path(checkout).resolve())

    installed = {
        re.sub(r"[-_.]+", "-", distribution.metadata["Name"].lower())
        for distribution in importlib.metadata.distributions()
    }
    assert {"cadquery-ocp-novtk", "pyopengl", "pyqt5", "pyqt5-sip"} <= installed
    assert not installed.intersection({"vtk", "zenframe", "termin"})

    for module_name in (
        "OpenGL.GL",
        "PyQt5.QtWidgets",
        "zencad.gui.display",
        "zencad.gui.mainwindow",
        "zencad.gui.settingswdg",
    ):
        importlib.import_module(module_name)

    if sys.platform.startswith("linux"):
        from OCP.Xw import Xw_Window  # noqa: F401
    elif sys.platform.startswith("win"):
        from OCP.WNT import WNT_Window  # noqa: F401
    elif sys.platform == "darwin":
        from OCP.Cocoa import Cocoa_Window  # noqa: F401
    else:
        raise AssertionError(f"Unsupported smoke-test platform: {sys.platform}")

    print(f"Installed GUI wheel import smoke on {sys.platform}: OK")


if __name__ == "__main__":
    main()
