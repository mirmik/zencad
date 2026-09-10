# Installation

ZenCad is installed from PyPI together with a prebuilt geometry-backend wheel.
Conda and a separate OpenCascade installation are not required.

## Graphical interface
```console
python3 -m pip install "zencad[gui]"
zencad
```

On Debian and Ubuntu, install the Qt/X11 system libraries before the first
run:

```console
sudo apt update
sudo apt install libglu1-mesa libxcb-cursor0 libxcb-icccm4 \
  libxcb-image0 libxcb-keysyms1 libxcb-randr0 libxcb-render-util0 \
  libxcb-shape0 libxcb-xfixes0 libxcb-xinerama0 libxcb-xkb1 \
  libxkbcommon-x11-0
```

The GUI uses X11; a Wayland session therefore needs XWayland.

## Headless geometry only
```console
python3 -m pip install zencad
```

ZenCad requires 64-bit CPython 3.10–3.14. Headless geometry wheels cover
Windows x86-64, macOS 11+ x86-64/arm64, and Linux x86-64/aarch64 with glibc
2.31 or newer. The GUI extra is available on Windows x86-64, macOS
x86-64/arm64, and Linux x86-64; PyQt5 does not currently publish Linux
aarch64 wheels.

## Current version from source

This guide describes the current ZenCad 2 source tree. `pip install zencad`
selects the published package, not necessarily this revision. In a checkout:

```sh
python -m pip install -e ".[gui]"
python -m zencad
```

For geometry only, use `python -m pip install -e .`. Optional example dependencies:
`python -m pip install -e ".[examples]"`.

Package version `2.0.0` does not imply completed platform acceptance.
Windows/macOS rendering still needs verification; Linux GUI needs working X11/OpenGL.
