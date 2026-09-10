# Installation

ZenCad installs from PyPI together with a binary wheel of the geometry backend. Neither Conda nor a separate OpenCascade installation is required.

## Graphical interface
```console
python3 -m pip install "zencad[gui]"
zencad
```

On Debian and Ubuntu, install the Qt/X11 system libraries before the first launch:

```console
sudo apt update
sudo apt install libglu1-mesa libxcb-cursor0 libxcb-icccm4 \
  libxcb-image0 libxcb-keysyms1 libxcb-randr0 libxcb-render-util0 \
  libxcb-shape0 libxcb-xfixes0 libxcb-xinerama0 libxcb-xkb1 \
  libxkbcommon-x11-0
```

The graphical interface uses X11; a Wayland session requires XWayland.

## Geometry only, without GUI
```console
python3 -m pip install zencad
```

64-bit CPython 3.10–3.14 is required. Geometry wheels are available for Windows x86-64, macOS 11+ x86-64/arm64, and Linux x86-64/aarch64 with glibc 2.31 or newer. The GUI extra is available for Windows x86-64, macOS x86-64/arm64 and Linux x86-64; PyQt5 currently provides no Linux aarch64 wheel.

## Current version from source

This manual describes the current ZenCad 2 source tree. `pip install zencad` retrieves the published package, which may not match this revision. In a checkout:

```sh
python -m pip install -e ".[gui]"
python -m zencad
```

For geometry only, use `python -m pip install -e .`. Install optional example dependencies with `python -m pip install -e ".[examples]"`.
