:ru
# Переход с ZenCad 1

Функциональность геометрии сохраняется, но типы, материализация и некоторые исторические ошибки намеренно изменены. Сверяйте пользовательские скрипты с этой таблицей, а не переносите старые настройки lazy.

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

Geometry capabilities are retained, but types, materialization and some historical defects intentionally change. Use this table instead of copying old lazy settings.

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
