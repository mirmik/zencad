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
## Текущая версия из исходников

Это руководство описывает текущее исходное дерево ZenCad 2. `pip install zencad`
получает опубликованный пакет, а не обязательно эту ревизию. В checkout:

```sh
python -m pip install -e ".[gui]"
python -m zencad
```

Без GUI используйте `python -m pip install -e .`. Дополнительные зависимости
примеров: `python -m pip install -e ".[examples]"`.

Номер `2.0.0` в метаданных не означает завершённую платформенную приёмку.
Windows/macOS-render ещё проверяется; Linux GUI требует рабочего X11/OpenGL.
