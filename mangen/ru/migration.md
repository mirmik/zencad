:ru
# Переход с ZenCad 1

При переносе скриптов учитывайте изменения типов, материализации и доступных обёрток геометрических операций. Сверяйте пользовательские скрипты с этой таблицей, а не переносите старые настройки lazy.

| Раньше | ZenCad 2 |
| --- | --- |
| `shape.unlazy()` перед вызовом OCCT | `shape.native()` возвращает объект OCP; сама форма уже имеет устойчивый тип |
| Раскрытие числового результата | `shape.mass().value()` или `float(shape.mass())` |
| `zencad.lazy.onplace = True` | `zencad.set_evaluation_mode("immediate")` в начале скрипта |
| Настройки чтения/записи через `zencad.lazy` | `zencad.configure(cache_enabled=False)` отключает дисковый кэш |
| `Runtime` с CAD-методами | Модульные функции `zencad.box(...)` и методы объектов |
| Наследование Point/Vector от NumPy | `point.to_numpy()`, `vector.to_numpy()` или `.value()` |
| `faces()[:4]` как «четыре боковые грани» | Геометрический селектор, например `filter_by_position(Axis.Z, height / 2)` |
| Callback с доступом к `DisplayWidget` | `state.input`, `state.camera` и контроллеры `display()` |
| Вызов `zencad.color(...)` | `zencad.Color(...)`; `zencad.color` — модуль |
| Имена `time`, `math`, `numpy`, случайно попавшие через `import *` | Явные импорты соответствующих модулей |

Совместимость с `zencad.lazy` намеренно не поддерживается в ZenCad 2. Старый пользовательский `@lazy` не имеет автоматической совместимой замены. Новые доменные операции используют `@zencad.operation`; описание деклараций находится в исходнике `zencad/operation.py` и development-документах. Не следует механически переименовывать декоратор.

## Геометрические массивы и сборки

Аргумент `unit=True` удалён из `multitrans`, `multitransform`, `sqrmirror`, `sqrtrans`, `rotate_array` и `rotate_array2`. Геометрические функции работают с формами и не создают сборочные или кинематические объекты. При `array=True` они возвращают отдельные копии; по умолчанию — их булево объединение.

Для сохранения отдельных деталей в сборке создайте юнит явно:

```python
from zencad import *
from zencad.assemble import unit

part = box(2).right(5)
copies = rotate_array(4, array=True)(part)
assembly = unit(parts=copies)
body = union(copies)
assert len(copies) == 4
assert abs(float(body.mass()) - 32) < 1e-7
```

Сборка зависит от геометрии, а геометрия не зависит от сборок. Вместо передачи интерактивного объекта или юнита в массив преобразований передавайте геометрическую форму и затем добавляйте её копии в сборку. `multitransform` — строчная функция создания `MultiTransform`, `sqrtrans` — синоним `sqrmirror`.

## Граф и явные границы

```python
import zencad as z

z.configure(cache_enabled=False)
body = z.box(10)
volume = body.mass()                  # Scalar, а не float
moved = body.right(volume / 100)      # зависимость остаётся в графе
assert isinstance(volume, z.Scalar)
assert abs(float(volume) - 1000) < 1e-7
ocp_shape = moved.native()            # вычисление для интеграции с OCP
```

`native()` возвращает native-значение, а не «старую оболочку Shape». Для последующих операций ZenCad сохраняйте исходный handle. `Point + Point` недопустимо; `Point - Point` возвращает `Vector`, `Vector + Vector` — `Vector`. Координаты `.x/.y/.z` имеют тип `Scalar`.

`len()` и итерация коллекций топологии вычисляют их; индексирование, срезы и селекторы сохраняют граф. Индексы не являются постоянными идентификаторами граней после редактирования геометрии.

## Анимация и кэш

В managed callback нельзя добавлять или заменять геометрию после начального `show()`. Создавайте объекты заранее, затем меняйте их размещение, цвет и видимость. `preanimate` и произвольный доступ к Qt не входят в managed-контракт. [Подробности](animate.html).

Кэш общий для процессов текущего пользователя. Старые записи кэша не являются совместимым форматом и могут быть отброшены. `set_evaluation_mode()` — обычная функция, не context manager; ранее предложенные `eager()`/`immediate()`/`evaluation()` context managers удалены. [Вычисления](caching.html).
:en
# Migrating from ZenCad 1

When migrating scripts, account for changes in types, materialization, and available geometry operation wrappers. Use this table instead of copying old lazy settings.

| Before | ZenCad 2 |
| --- | --- |
| `shape.unlazy()` before OCCT access | `shape.native()` returns an OCP object; the shape already has a stable type |
| Unwrapping numeric results | `shape.mass().value()` or `float(shape.mass())` |
| `zencad.lazy.onplace = True` | `zencad.set_evaluation_mode("immediate")` in the script header |
| Cache toggles on `zencad.lazy` | `zencad.configure(cache_enabled=False)` disables disk caching |
| CAD methods on `Runtime` | Module functions such as `zencad.box(...)` and domain methods |
| NumPy-derived Point/Vector objects | `point.to_numpy()`, `vector.to_numpy()` or `.value()` |
| `faces()[:4]` meaning “four side faces” | A geometric selector such as `filter_by_position(Axis.Z, height / 2)` |
| Callback access to `DisplayWidget` | `state.input`, `state.camera` and `display()` controllers |
| Calling `zencad.color(...)` | `zencad.Color(...)`; `zencad.color` is a module |
| Accidental `time`, `math`, `numpy` wildcard exports | Explicit imports of those modules |

ZenCad 2 intentionally does not provide compatibility with `zencad.lazy`. The former user `@lazy` decorator has no automatic compatible replacement. New domain operations use `@zencad.operation`; declarations are described in `zencad/operation.py` and development documents. Do not mechanically rename decorators.

## Geometry patterns and assemblies

The `unit=True` argument is removed from `multitrans`, `multitransform`, `sqrmirror`, `sqrtrans`, `rotate_array` and `rotate_array2`. Geometry functions operate on shapes and do not create assembly or kinematic objects. With `array=True` they return separate copies; by default they return their boolean union.

Create an explicit unit to keep separate assembly parts:

```python
from zencad import *
from zencad.assemble import unit

part = box(2).right(5)
copies = rotate_array(4, array=True)(part)
assembly = unit(parts=copies)
body = union(copies)
assert len(copies) == 4
assert abs(float(body.mass()) - 32) < 1e-7
```

Assemblies depend on geometry; geometry does not depend on assemblies. Pass geometric shapes to transform patterns, then put their copies into an assembly, instead of passing interactive objects or units to the pattern. `multitransform` is a lowercase factory for `MultiTransform`; `sqrtrans` is a synonym for `sqrmirror`.

## Graphs and explicit boundaries

```python
import zencad as z

z.configure(cache_enabled=False)
body = z.box(10)
volume = body.mass()                  # Scalar, not float
moved = body.right(volume / 100)      # retains the dependency
assert isinstance(volume, z.Scalar)
assert abs(float(volume) - 1000) < 1e-7
ocp_shape = moved.native()            # materialize for OCP integration
```

`native()` returns a native value, not an older Shape wrapper. Keep the original handle for further ZenCad operations. `Point + Point` is invalid; `Point - Point` produces `Vector`, and `Vector + Vector` produces `Vector`. Coordinates `.x/.y/.z` are `Scalar` values.

`len()` and iteration materialize topology collections; indexing, slicing and selectors retain the graph. Indices are not persistent face identities across model edits.

## Animation and caching

Managed callbacks cannot add or replace geometry after initial `show()`. Create objects first, then change placement, color and visibility. `preanimate` and arbitrary Qt access are outside the managed contract. [Details](animate.html).

Processes of the same user share a cache. Old cache records are disposable, not a compatible format. `set_evaluation_mode()` is a regular function, not a context manager; the previously proposed `eager()`/`immediate()`/`evaluation()` context managers are removed. [Evaluation](caching.html).
::

:ru
## Исторические операции кривых

В старых руководствах встречаются `curve.length()`, `curve.linoff(u, dist)` и `curve.linoff_point(u, dist)`. Они обозначали длину кривой, параметр после смещения на заданную длину и соответствующую точку. В текущем `Curve` таких методов нет. Для равномерного разбиения используйте `uniform()` или `uniform_points()`; это не замена смещению на произвольное расстояние.

Длину и смещение по длине можно вычислить через OCP. `curve.native()` материализует кривую, результат вычисления OCP — обычное число, не зависимый `Scalar`. Начальный параметр и расстояние выбирайте внутри диапазона конечной кривой; перед чтением результата проверяйте `IsDone()`.
:en
## Historical curve operations

Older manuals mention `curve.length()`, `curve.linoff(u, dist)`, and `curve.linoff_point(u, dist)`: curve length, the parameter after an arc-length offset, and the corresponding point. These methods are not present on the current `Curve`. Use `uniform()` or `uniform_points()` for equally spaced samples; sampling is not a replacement for an arbitrary distance offset.

Use OCP to calculate length and arc-length offsets. `curve.native()` materializes the curve; OCP returns an ordinary number, not a dependent `Scalar`. Choose the initial parameter and distance within the finite curve domain, and check `IsDone()` before reading the result.
::

```python
import math
from zencad import *
from OCP.GeomAdaptor import GeomAdaptor_Curve
from OCP.GCPnts import GCPnts_AbscissaPoint

curve = circle(5, wire=True).curve()
interval = curve.range()
start, end = float(interval.lower), float(interval.upper)
adaptor = GeomAdaptor_Curve(curve.native(), start, end)
length = GCPnts_AbscissaPoint.Length_s(adaptor, start, end)
solver = GCPnts_AbscissaPoint(adaptor, length / 4, start)
assert solver.IsDone()
parameter = solver.Parameter()
point = curve.point(parameter)
assert abs(length - 10 * math.pi) < 1e-7
assert abs(float(point.x)) < 1e-7
assert abs(float(point.y) - 5) < 1e-7
```

:ru
## Историческая функция tube

Старая `tube(spine, r)` строила боковую оболочку круглого профиля, а не трубу с толщиной стенки. Для такой поверхности используйте `pipe_shell([profile], spine, solid=False)`. Профиль должен находиться в начале траектории и быть перпендикулярен её касательной. В примере ниже траектория направлена по Z, а круг лежит в XY.

`solid=True` создаёт закрытое тело. Для трубы с толщиной стенки вычтите развёртку меньшего радиуса, как в разделе [Траекторная развёртка](sweep.html). Старые `bounds=True` и параметры аппроксимации `tol`, `cont`, `maxdegree`, `maxsegm` не имеют одноимённой автоматической замены: `pipe_shell` возвращает одну форму, не кортеж с граничными рёбрами.
:en
## Historical tube function

The old `tube(spine, r)` constructed the lateral shell of a circular profile, not a tube with wall thickness. Use `pipe_shell([profile], spine, solid=False)` for that surface. Position the profile at the spine start, perpendicular to its tangent. The example uses a Z-directed spine and an XY circle.

`solid=True` constructs a capped solid. For a tube with wall thickness, subtract a smaller-radius sweep as in [Sweeps](sweep.html). The old `bounds=True` and approximation parameters `tol`, `cont`, `maxdegree`, `maxsegm` have no automatic same-named replacements: `pipe_shell` returns one shape, not a tuple including boundary edges.
::

```python
from zencad import *

spine = segment((0, 0, 0), (0, 0, 20))
profile = circle(3, wire=True)
surface = pipe_shell([profile], spine, solid=False)
body = pipe_shell([profile], spine)
assert isinstance(surface, Shell)
assert isinstance(body, Solid)
surface.assert_valid()
body.assert_valid()
```
