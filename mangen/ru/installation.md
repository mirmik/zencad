:ru
# Установка

ZenCad устанавливается из PyPI вместе с готовым бинарным wheel геометрического
backend. Conda и отдельная установка OpenCascade не требуются.

## Графический интерфейс
```console
python3 -m pip install "zencad[gui]"
zencad
```

## Только геометрия, без GUI
```console
python3 -m pip install zencad
```

Поддерживаются CPython 3.10–3.14, Windows x86-64, macOS 11+
x86-64/arm64 и Linux x86-64/aarch64 с glibc 2.31 или новее.
:en
# Installation

ZenCad is installed from PyPI together with a prebuilt geometry-backend wheel.
Conda and a separate OpenCascade installation are not required.

## Graphical interface
```console
python3 -m pip install "zencad[gui]"
zencad
```

## Headless geometry only
```console
python3 -m pip install zencad
```

Supported wheels cover CPython 3.10–3.14, Windows x86-64, macOS 11+
x86-64/arm64, and Linux x86-64/aarch64 with glibc 2.31 or newer.
