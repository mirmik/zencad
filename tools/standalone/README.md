# ZenCad standalone for Linux

The bundle includes Python, OCP, Qt and the `gui` and `examples` dependencies.
It does not use the Python installation on your machine. Additional packages
installed with your system's pip are not available inside this bundle.

## Run

Make the AppImage executable and open it, or pass a model:

```sh
chmod +x ZenCad-2.0.0-linux-x86_64.AppImage
./ZenCad-2.0.0-linux-x86_64.AppImage model.py
```

For the tar.gz archive, extract the whole `ZenCad` directory and run
`./ZenCad/ZenCad`. Keep `_internal` next to the executable.

The same command supports `inspect`, `check`, `render`, `--no-show` and
`--display`. Examples are available from the GUI menu.

If FUSE is unavailable, use `--appimage-extract-and-run`. For repeated launches,
extract once with `--appimage-extract` and run `squashfs-root/AppRun`.

## Linux requirements

The build targets x86_64, Ubuntu 22.04 or newer (glibc 2.35+), with the system
C++ runtime and OpenGL drivers. The GUI uses X11 or XWayland. Python and Qt
are bundled; graphics drivers and glibc come from the host.

## Build from source

From the repository root, with Docker and Python 3 installed:

```sh
sh tools/build_standalone_linux.sh
```

Results are written to `standalone-dist`: a directory, tar.gz archive,
AppImage and `SHA256SUMS`. The PyPI artifacts in `dist` are preserved.
`build-info.json` records the source revision and installed dependency versions.
The Ubuntu 22.04 Dockerfile and Python constraints are in `tools/standalone`.

AppImage tooling downloads are checked against pinned SHA-256 hashes.
The upstream `type2-runtime` continuous asset can change: if its checksum
changes, review the new release before updating the pin, or reuse the cached
verified asset in `build/appimage-tools`.

To check the directory or AppImage outside the checkout:

```sh
LIBGL_ALWAYS_SOFTWARE=1 xvfb-run -a python3 utest/frozen_smoke.py standalone-dist/ZenCad/ZenCad
LIBGL_ALWAYS_SOFTWARE=1 xvfb-run -a python3 utest/frozen_smoke.py standalone-dist/ZenCad-2.0.0-linux-x86_64.AppImage --extract-and-run
```

The smoke covers geometry inspection, validation, PNG rendering, bundled
resources and example dependencies, 20 GUI reloads, cancellation, changing
models and animation. `--headless` skips tests that need an X server.

Verified on 2026-09-12: the complete smoke on Ubuntu 24.04 under Xvfb;
inspect, render and GUI reload on a clean Ubuntu 22.04 container without
Python or Qt. The runtime-only test image is `Dockerfile.smoke`. AppImage
checks used extraction mode; FUSE mounting was not available in the test host.

## Licenses and sources

ZenCad source code is MIT-licensed. Bundled components retain their own
licenses: in particular, PyQt5 is GPLv3 and Qt is LGPLv3. The standalone
distribution includes these components; the MIT license of ZenCad alone
does not describe the entire bundle.

Python package metadata and available notices are preserved under
`_internal/*.dist-info`; system library notices and additional upstream
licenses are in `licenses`. The shipped ZenCad Python sources, including
examples and their attribution files, are under `_internal/zencad`.

Source locations:

- ZenCad and the build scripts: https://github.com/mirmik/zencad
- Python: https://www.python.org/downloads/source/
- PyQt5: https://pypi.org/project/PyQt5/5.15.11/#files
- Qt: https://download.qt.io/archive/qt/5.15/5.15.19/submodules/
- OCP: https://github.com/CadQuery/OCP
- OCP no-VTK wheels: https://pypi.org/project/cadquery-ocp-novtk/7.9.3.1.1/
- OCCT: https://github.com/Open-Cascade-SAS/OCCT/tree/V7_9_3
- PyInstaller: https://github.com/pyinstaller/pyinstaller/tree/v6.22.0
- AppImage runtime: https://github.com/AppImage/type2-runtime/tree/75849dce7cc37e4319b633df1f116ca895c71a12

The Ubuntu Mono font and the Bulbasaur model have separate license and
attribution files alongside the examples. Bulbasaur is CC BY-NC-SA 4.0.
