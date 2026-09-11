# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path
import sys
from PyInstaller.utils.hooks import collect_data_files, collect_submodules, copy_metadata

root = Path(SPECPATH)
datas = collect_data_files("zencad", include_py_files=True)
# Keep installed dependency versions and their bundled license notices.
datas += copy_metadata("zencad", recursive=True)
hiddenimports = ["PyQt5.QtTest", "unittest.mock"]
hiddenimports += collect_submodules("OpenGL.platform")
hiddenimports += collect_submodules("OpenGL.arrays")
# User models import modules dynamically, outside PyInstaller's import graph.
for package in ("zencad", "OCP", "PIL", "skimage", "trimesh"):
    hiddenimports += collect_submodules(
        package,
        filter=lambda name: not any(part in ("tests", "testing", "examples")
                                    for part in name.split(".")),
    )
for distribution in ("PyQt5", "PyQt5-Qt5", "PyQt5-sip", "PyOpenGL",
                     "Pillow", "scikit-image", "trimesh"):
    datas += copy_metadata(distribution, recursive=True)

a = Analysis(
    [str(root / "tools/standalone/entry.py")],
    pathex=[str(root)],
    datas=datas,
    hiddenimports=hiddenimports,
    excludes=["tkinter", "matplotlib", "IPython", "pytest"],
)
if sys.platform.startswith("linux"):
    # The system's GL drivers may need a newer C++ runtime than the builder.
    # Ubuntu 22.04+ provides the runtime needed by the bundled libraries.
    a.binaries = [entry for entry in a.binaries
                  if Path(entry[0]).name not in ("libstdc++.so.6", "libgcc_s.so.1")]
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name="ZenCad",
          console=True, strip=False, upx=False)
coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=False, name="ZenCad")
