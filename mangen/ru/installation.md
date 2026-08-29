:ru
# Установка

ZenCad устанавливается из PyPI вместе с готовым бинарным wheel геометрического
backend. Conda и отдельная установка OpenCascade не требуются.

## Графический интерфейс
```console
python3 -m pip install "zencad[gui]"
zencad
```

В Debian и Ubuntu перед первым запуском установите системные библиотеки Qt/X11:

```console
sudo apt update
sudo apt install libglu1-mesa libxcb-cursor0 libxcb-icccm4 \
  libxcb-image0 libxcb-keysyms1 libxcb-randr0 libxcb-render-util0 \
  libxcb-shape0 libxcb-xfixes0 libxcb-xinerama0 libxcb-xkb1 \
  libxkbcommon-x11-0
```

Графический интерфейс использует X11; в Wayland-сессии требуется XWayland.

## Только геометрия, без GUI
```console
python3 -m pip install zencad
```

Требуется 64-битный CPython 3.10–3.14. Геометрическая часть имеет готовые
wheel для Windows x86-64, macOS 11+ x86-64/arm64 и Linux x86-64/aarch64 с
glibc 2.31 или новее. GUI-extra доступен для Windows x86-64, macOS
x86-64/arm64 и Linux x86-64; PyQt5 сейчас не публикует wheel для Linux
aarch64.
:en
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
