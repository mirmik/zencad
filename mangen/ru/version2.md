:ru
# Чем ZenCad 2 отличается от ZenCad 1

ZenCad 2 сохраняет скриптовый способ моделирования на Python, но меняет установку геометрического backend, устройство визуализатора и представление результатов вычислений. Эти изменения упрощают установку, отделяют вычисление модели от её отображения и делают API более предсказуемым для человека и программных инструментов.

## Геометрическое ядро и установка из PyPI

Само геометрическое ядро остаётся **OpenCascade**. Меняется способ доступа к нему из Python: вместо `pythonocc-core` используются привязки `cadquery-ocp-novtk` с модулями `OCP`.

В ZenCad 1 установка геометрических зависимостей требовала отдельного внимания к поставке `pythonocc-core` и OpenCascade. В ZenCad 2 backend поставляется готовыми бинарными wheel через PyPI и устанавливается как зависимость ZenCad. Для поддерживаемых платформ не нужно отдельно собирать OpenCascade или создавать окружение Conda.

```sh
python3 -m pip install "zencad[gui]"
```

Это команда установки опубликованного пакета. Если нужная ревизия ZenCad 2 ещё не опубликована, используйте установку из исходников. Варианты установки и требования к платформе описаны в разделе [«Установка»](installation.html).

## Постоянный viewer вместо встраиваемых окон

В ZenCad 1 процесс модели создавал собственное окно визуализации, которое встраивалось в главное окно приложения. Пересчёт модели затрагивал не только вычисления, но и жизненный цикл этого окна. Такая схема зависела от механизмов оконной системы.

В редакторе ZenCad 2 viewer принадлежит главному GUI-процессу и сохраняется между запусками скрипта. В этом процессе находятся Qt, OpenGL, камера и объекты отображения OpenCascade. Отдельный исполнитель модели занимается геометрией и не создаёт окно, которое нужно встраивать.

| ZenCad 1 | ZenCad 2 |
| --- | --- |
| Процесс модели создаёт окно viewer. | Процесс модели собирает данные сцены. |
| Главное окно встраивает окно другого процесса. | Главное окно отображает данные в собственном постоянном viewer. |
| Перезапуск вычислений связан с заменой окна модели. | Перезапускается исполнитель; viewer и камера сохраняются. |

При прямом запуске `python model.py` вызов `show()` открывает самостоятельный viewer в процессе скрипта. Описанное разделение GUI и исполнителя относится к работе редактора.

## Как геометрия передаётся между процессами

Исполнитель собирает описание сцены: формы, их размещение, цвета, видимость и имена. BREP-геометрия сериализуется в байты; меши передаются как данные вершин и треугольников. Вместе с параметрами отображения они образуют снимок сцены `SceneSnapshot`, который передаётся по межпроцессному протоколу.

GUI декодирует снимок и создаёт собственные объекты отображения AIS. Через границу процессов передаются **данные геометрии**, а не окно, указатели на объекты OpenCascade или объекты Qt.

Каждый запуск имеет номер поколения. GUI принимает результат актуального запуска; запоздавший результат предыдущего пересчёта не заменит текущую сцену. Во время вычисления или при ошибке остаётся видимым последний успешный результат. В анимации изменения размещения, цвета и видимости передаются отдельными обновлениями, без повторной передачи всей геометрии на каждом кадре.

Это же представление сцены используется для автоматического анализа: `inspect` и `check` могут получить результат модели без запуска viewer. Подробности — в разделах [«Внутренняя кухня»](internal.html) и [«Работа с агентом»](agents.html).

## Типы объектов и ленивые вычисления

В ZenCad 1 ленивость была видна в типах результатов: отложенные операции могли возвращать оболочки `LazyObject` и `LazyObjectShape`. Основным представлением топологических объектов служил `Shape`; `point3` и `vector3` были классами, наследующимися от NumPy-массива.

В ZenCad 2 публичные объекты сохраняют свой тип независимо от режима вычислений. Тела, грани, рёбра и вершины представлены типами `Solid`, `Face`, `Edge`, `Vertex`; числа, точки и векторы — `Scalar`, `Point3`, `Vector3` и другими типами значений. Ленивый граф хранится внутри этих объектов. Переключение `deferred`/`immediate` и включение кэша не подменяют их классы.

Для создания значений в скриптах используются строчные функции:

```python
from zencad import *

p = point3(1, 2, 3)
v = vector3(4, 0, 0)
body = box(10)
volume = body.mass()

assert isinstance(p, Point3)
assert isinstance(body, Solid)
assert isinstance(volume, Scalar)
assert (p + v).value() == (5, 2, 3)
assert abs(float(volume) - 1000) < 1e-7
```

`point3` теперь является функцией создания `Point3`, а не самим классом. Точки и векторы не являются NumPy-массивами: для получения массива используется `.to_numpy()`. Численное значение запрашивается через `.value()` или `float()`, форма OCP — через `.native()`.

Запросы топологии возвращают коллекции `ShapeList` с определённым типом элементов. Например, `body.faces()` содержит `Face`, а `body.vertices()` — `Vertex`; координаты вершины доступны через `.point()`. Индексирование и селекторы сохраняют зависимости, а итерация и запрос длины коллекции требуют вычисления.

## Система ленивых вычислений: EvalCache v2

ZenCad 1 использовал механизм `Lazy` и универсальные оболочки `LazyObject`. Настройки вычисления и кэширования задавались через объект `zencad.lazy`; пользовательские функции можно было оборачивать декоратором `@lazy`.

ZenCad 2 использует вычислитель **EvalCache v2**. Операции образуют граф с явно описанными типами результатов и правилами их сохранения. Публичный геометрический объект содержит значение или выражение этого графа. Поэтому ленивость сохраняется, но пользователь работает с объектом `Solid`, `Point3` или `Scalar`, а не с универсальной оболочкой.

Зависимости могут проходить и через численные результаты. Например, объём одного тела можно использовать при построении другого, не преобразуя его заранее в Python-число:

```python
from zencad import *

body = box(10)
volume = body.mass()
moved = body.right(volume / 100)
assert abs(float(moved.center().x) - 15) < 1e-7
```

`volume / 100` остаётся зависимостью в графе; явный `float()` запрашивает вычисленное число. Граф также доступен для диагностики: `inspect --tree` показывает операции и зависимости, а `--failed-path` помогает найти путь к сбойному вычислению.

Режим выполнения и кэш задаются независимо:

- `set_evaluation_mode("deferred")` откладывает вычисления до запроса результата; `set_evaluation_mode("immediate")` выполняет операции при построении.
- `configure(cache_enabled=True)` разрешает дисковый кэш, а `False` отключает его чтение и запись, не отключая сам граф зависимостей.

Сочетания этих настроек разобраны в таблице раздела [«Вычисления и кэш»](caching.html). Файлы кэша ZenCad 1 не являются совместимым кэшем ZenCad 2.

Совместимость со старым объектом `zencad.lazy` и декоратором `@lazy` не поддерживается. Конкретные замены вызовов и правила адаптации скриптов приведены отдельно в [«Миграции с ZenCad 1»](migration.html).
:en
# How ZenCad 2 differs from ZenCad 1

ZenCad 2 retains Python scripting for modeling, while changing geometry-backend installation, viewer architecture and the representation of computation results. These changes simplify installation, separate model evaluation from presentation and make the API more predictable for people and software tools.

## Geometry kernel and installation from PyPI

The geometry kernel itself remains **OpenCascade**. Its Python bindings change from `pythonocc-core` to `cadquery-ocp-novtk`, exposed through the `OCP` modules.

In ZenCad 1, geometry dependencies required separate attention to the distribution of `pythonocc-core` and OpenCascade. In ZenCad 2, the backend is distributed as prebuilt binary wheels through PyPI and installed as a ZenCad dependency. Supported platforms do not require a separate OpenCascade build or a Conda environment.

```sh
python3 -m pip install "zencad[gui]"
```

This installs the published package. If the desired ZenCad 2 revision has not been published yet, install from source. See [Installation](installation.html) for installation options and platform requirements.

## A persistent viewer instead of embedded windows

In ZenCad 1, the model process created its own viewer window, which was embedded in the application's main window. Re-evaluating a model affected both computation and the lifecycle of that window. This design depended on window-system mechanisms.

In the ZenCad 2 editor, the viewer belongs to the main GUI process and persists across script runs. Qt, OpenGL, the camera and OpenCascade presentation objects live in that process. A separate model runner computes geometry without creating a window to embed.

| ZenCad 1 | ZenCad 2 |
| --- | --- |
| The model process creates a viewer window. | The model process collects scene data. |
| The main window embeds another process's window. | The main window displays data in its own persistent viewer. |
| Restarting computation involves replacing the model window. | The runner restarts; the viewer and camera persist. |

When running `python model.py` directly, `show()` opens a standalone viewer in the script process. The GUI/runner separation described here applies to the editor.

## How geometry crosses process boundaries

The runner collects a scene description: shapes, placements, colors, visibility and names. BREP geometry is serialized to bytes; meshes are transmitted as vertex and triangle data. Together with presentation properties, these form a `SceneSnapshot` sent through the interprocess protocol.

The GUI decodes the snapshot and creates its own AIS presentation objects. The process boundary carries **geometry data**, not a window, OpenCascade object pointers or Qt objects.

Each run has a generation number. The GUI accepts the current run's result; a late result from an earlier evaluation cannot replace the current scene. The last successful result remains visible during computation or on failure. Animations send placement, color and visibility updates without retransmitting all geometry on each frame.

The same scene representation supports automated analysis: `inspect` and `check` can obtain a model's result without starting a viewer. See [ZenCad internals](internal.html) and [Working with an agent](agents.html).

## Object types and lazy evaluation

In ZenCad 1, laziness was visible in result types: deferred operations could return `LazyObject` and `LazyObjectShape` wrappers. `Shape` was the main representation of topology objects; `point3` and `vector3` were classes derived from NumPy arrays.

In ZenCad 2, public objects retain their types regardless of evaluation mode. Solids, faces, edges and vertices use types such as `Solid`, `Face`, `Edge` and `Vertex`; numbers, points and vectors use `Scalar`, `Point3`, `Vector3` and other value types. Objects retain their lazy graphs internally. Switching between `deferred` and `immediate`, or enabling caching, does not replace their classes.

Scripts construct values with lowercase functions:

```python
from zencad import *

p = point3(1, 2, 3)
v = vector3(4, 0, 0)
body = box(10)
volume = body.mass()

assert isinstance(p, Point3)
assert isinstance(body, Solid)
assert isinstance(volume, Scalar)
assert (p + v).value() == (5, 2, 3)
assert abs(float(volume) - 1000) < 1e-7
```

`point3` is now a function constructing a `Point3`, rather than the class itself. Points and vectors are not NumPy arrays; use `.to_numpy()` to obtain an array. Request numeric values with `.value()` or `float()`, and an OCP shape with `.native()`.

Topology queries return `ShapeList` collections with specific element types. For example, `body.faces()` contains `Face` objects, while `body.vertices()` contains `Vertex` objects; use `.point()` to obtain vertex coordinates. Indexing and selectors retain dependencies, while iteration and collection length require evaluation.

## Lazy evaluation: EvalCache v2

ZenCad 1 used `Lazy` and generic `LazyObject` wrappers. Evaluation and caching were configured through `zencad.lazy`, and user functions could be wrapped with `@lazy`.

ZenCad 2 uses the **EvalCache v2** evaluator. Operations form a graph with explicitly declared result types and serialization rules. Public geometry objects contain either a value or an expression in that graph. Evaluation remains lazy, but users work with `Solid`, `Point3` or `Scalar` objects instead of generic wrappers.

Dependencies can also pass through numeric results. For example, one shape's volume can participate in another operation without first converting it to a Python number:

```python
from zencad import *

body = box(10)
volume = body.mass()
moved = body.right(volume / 100)
assert abs(float(moved.center().x) - 15) < 1e-7
```

`volume / 100` retains the graph dependency; an explicit `float()` requests the computed number. The graph also supports diagnostics: `inspect --tree` shows operations and dependencies, while `--failed-path` helps trace a failed computation.

Execution mode and caching are configured independently:

- `set_evaluation_mode("deferred")` delays evaluation until a result is requested; `set_evaluation_mode("immediate")` evaluates operations as they are constructed.
- `configure(cache_enabled=True)` enables disk caching; `False` disables cache reads and writes without disabling the dependency graph.

The combinations are shown in the table in [Evaluation and caching](caching.html). ZenCad 1 cache files are not a compatible cache for ZenCad 2.

The old `zencad.lazy` object and `@lazy` decorator are not supported. Call replacements and script adaptation rules are described separately in [Migrating from ZenCad 1](migration.html).
::
