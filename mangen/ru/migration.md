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

## Исторические операции кривых

В старых руководствах встречаются `curve.length()`, `curve.linoff(u, dist)` и `curve.linoff_point(u, dist)`. Они обозначали длину кривой, параметр после смещения на заданную длину и соответствующую точку. В текущем `Curve` таких методов нет. Для равномерного разбиения используйте `uniform()` или `uniform_points()`; это не замена смещению на произвольное расстояние.

Длину и смещение по длине можно вычислить через OCP. `curve.native()` материализует кривую, результат вычисления OCP — обычное число, не зависимый `Scalar`. Начальный параметр и расстояние выбирайте внутри диапазона конечной кривой; перед чтением результата проверяйте `IsDone()`.

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

## Историческая функция tube

Старая `tube(spine, r)` строила боковую оболочку круглого профиля, а не трубу с толщиной стенки. Для такой поверхности используйте `pipe_shell([profile], spine, solid=False)`. Профиль должен находиться в начале траектории и быть перпендикулярен её касательной. В примере ниже траектория направлена по Z, а круг лежит в XY.

`solid=True` создаёт закрытое тело. Для трубы с толщиной стенки вычтите развёртку меньшего радиуса, как в разделе [Траекторная развёртка](sweep.html). Старые `bounds=True` и параметры аппроксимации `tol`, `cont`, `maxdegree`, `maxsegm` не имеют одноимённой автоматической замены: `pipe_shell` возвращает одну форму, не кортеж с граничными рёбрами.

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
