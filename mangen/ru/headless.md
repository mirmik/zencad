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
