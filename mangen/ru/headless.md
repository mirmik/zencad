:ru
# Автоматизация без редактора

Для `inspect` и `check` достаточно geometry-only установки. Скрипт должен объявить статическую сцену через `display()` и `show()`, как в [первой модели](helloworld.html). Код модели исполняется в отдельном процессе.

## Inspect и граф вычислений

```sh
zencad inspect model.py --json
zencad inspect model.py --output report.json
zencad inspect model.py --tree --no-cache
zencad inspect model.py --graph-json graph.json
zencad inspect model.py --tree --failed-path
```

Отчёт содержит ID и имена объектов, размещение, bounding box, типы и количество топологии, площадь/объём, статистику mesh, digest и валидность. `stdout`/`stderr` модели перенаправлены в stderr команды: stdout JSON можно передавать следующему инструменту.

Дерево показывает операции, общие зависимости, состояние кэша/вычислений и источник в коде. `--root`, `--max-depth`, `--hide-literals`, `--max-graph-nodes` ограничивают представление. При неподдерживаемой кодировке вывода ветви дерева печатаются в ASCII; API `to_tree()` сохраняет Unicode. `--graph-json` — отдельный формат графа, не отчёт геометрии.

## Проверяемые требования

```sh
zencad check model.py --valid --solid
zencad check model.py --volume 700:800 --bbox-size 19:21,9:11,3:5 --json
```

`--solid` требует solid-тип каждого видимого BREP-объекта; compound с телом внутри не равнозначен solid. Проверяется видимый результат; несколько объектов агрегируются по контракту команды. JSON содержит expected/actual/tolerance. Код `7` означает несоответствие требованиям при успешно исполненной модели; `0` — успех. Ошибка скрипта — `3`, геометрии/сцены — `4`, таймаут — `5`, ошибка вывода — `6`, неправильные аргументы — `2`. Подробности: [inspect](../development/headless-inspect.md), [check](../development/headless-check.md).

## Python API

```python
from zencad import inspect_script

if __name__ == "__main__":
    report = inspect_script("model.py", cache_enabled=False)
    print(report.to_json())
```

Защита entry point нужна из-за запуска дочернего процесса. Также доступны `check_script`, `inspect_computation_graph`, `render_script`; форматы и параметры описаны в development-справке.

## PNG-превью

```sh
zencad render model.py -o preview.png
zencad render model.py -o views.png --views iso,front,top,right --size 640x480
```

Ракурсы: `iso`, `front`, `back`, `left`, `right`, `top`, `bottom`. Размер задаётся для каждого тайла; несколько видов собираются в контактный лист. Камера ортографическая с новым FitAll, без сохранённого состояния редактора. Режимы: `shaded`, `shaded-with-edges`, `wireframe`; доступны фон, оси и margin.

Render требует `gui` extra и работоспособный OpenGL. На сервере Linux:

```sh
LIBGL_ALWAYS_SOFTWARE=1 xvfb-run -a zencad render model.py -o preview.png
```

Windows/macOS-render ещё требует платформенной приёмки; на GitHub-hosted macOS зафиксирован отказ создания OpenGL-контекста. Это не препятствует headless inspect/check, которым viewer не нужен. [Контракт рендера](../development/deterministic-render.md).
:en
# Automation without the editor

`inspect` and `check` need only the geometry installation. Scripts must declare a static scene with `display()` and `show()`, as in [your first model](helloworld.html). Model code runs in an isolated process.

## Inspection and computation graphs

```sh
zencad inspect model.py --json
zencad inspect model.py --output report.json
zencad inspect model.py --tree --no-cache
zencad inspect model.py --graph-json graph.json
zencad inspect model.py --tree --failed-path
```

Reports contain object IDs and names, placement, bounding boxes, topology types/counts, area/volume, mesh statistics, digests and validity. Model stdout/stderr is forwarded to command stderr, keeping JSON stdout suitable for pipelines.

Trees show operations, shared dependencies, cache/evaluation state and source locations. `--root`, `--max-depth`, `--hide-literals` and `--max-graph-nodes` bound the view. If the output encoding cannot represent tree branches, the CLI uses ASCII; API `to_tree()` retains Unicode. `--graph-json` is a separate graph format, not the geometry report.

## Verifiable requirements

```sh
zencad check model.py --valid --solid
zencad check model.py --volume 700:800 --bbox-size 19:21,9:11,3:5 --json
```

`--solid` requires each visible BREP object to have solid type; a compound containing a solid is not itself a solid. Checks target the visible result; multiple objects are aggregated according to the command contract. JSON includes expected/actual/tolerance. Exit `7` means an assertion failed after successful model execution; `0` means success. Script errors use `3`, geometry/scene errors `4`, timeouts `5`, output errors `6` and invalid arguments `2`. Details: [inspect](../development/headless-inspect.md), [check](../development/headless-check.md).

## Python API

```python
from zencad import inspect_script

if __name__ == "__main__":
    report = inspect_script("model.py", cache_enabled=False)
    print(report.to_json())
```

Protect the entry point because evaluation starts a child process. `check_script`, `inspect_computation_graph` and `render_script` are also available; see the development references for formats and parameters.

## PNG previews

```sh
zencad render model.py -o preview.png
zencad render model.py -o views.png --views iso,front,top,right --size 640x480
```

Views are `iso`, `front`, `back`, `left`, `right`, `top`, `bottom`. Size applies to each tile; multiple views form a contact sheet. Rendering uses an orthographic camera and fresh FitAll, independent of saved editor state. Modes are `shaded`, `shaded-with-edges`, `wireframe`; background, axes and margin are configurable.

Rendering requires the `gui` extra and working OpenGL. On a Linux server:

```sh
LIBGL_ALWAYS_SOFTWARE=1 xvfb-run -a zencad render model.py -o preview.png
```

Windows/macOS rendering still needs platform acceptance; GitHub-hosted macOS has shown OpenGL context creation failures. This does not prevent headless inspect/check, which need no viewer. [Rendering contract](../development/deterministic-render.md).
::
