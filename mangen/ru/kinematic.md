:ru
# Кинематика

Кинематика дополняет [сборки](assemble.html): положение деталей задаётся обобщёнными координатами — например, углом шарнира или ходом линейного привода. Геометрия деталей строится обычными функциями ZenCad, а кинематические звенья управляют их размещением.

## Два юнита одного звена

Кинематический компонент реализован парой юнитов, находящихся в относительном движении:

- Сам объект звена, наследующий `kinematic_unit`, служит входным юнитом. Его `location` задаёт установку звена относительно родителя.
- `joint.output` — выходной юнит, дочерний по отношению к входному. Его положение относительно входа определяется кинематическими координатами.

```text
parent
└── joint                 вход: установка шарнира
    └── joint.output      выход: вращение или перемещение
        └── payload       деталь или следующее звено
```

`joint.add(shape)` прикрепляет геометрию к входу, например корпус привода. `joint.output.add(shape)` прикрепляет её к подвижному выходу. Вызов `joint.link(child)` также присоединяет `child` к **выходу**, в отличие от `unit.link(child)`, который присоединяет непосредственно к текущему юниту.

При создании потомка через конструктор пишите `parent=joint.output`, если он должен двигаться вместе с выходом. `parent=joint` прикрепляет его к входному юниту.

## Вращательное и поступательное звенья

Классы импортируются из `zencad.assemble`:

| Звено | Координата | Движение выхода |
| --- | --- | --- |
| `rotator(axis=...)` | `set_coord(angle)`, угол в радианах | Вращение вокруг локальной оси входа |
| `actuator(axis=...)` | `set_coord(distance)`, длина в единицах модели | Перемещение вдоль локальной оси входа |

Ось нормируется. Параметр `mul` масштабирует координату: фактический угол или ход равен `coord * mul`. `location` устанавливает вход звена, а `set_coord()` изменяет относительное положение выхода. У однокоординатных звеньев `dim()` возвращает `1`; доступна также запись `set_coords([value])`.

Пример поворотного рычага:

```python
from zencad import *
from zencad.assemble import unit, rotator

base = unit()
joint = rotator(axis=(0, 0, 1), parent=base)
joint.add(cylinder(3, 2, center=True))
joint.output.add(box(20, 2, 2).back(1).down(1))
tip = unit(parent=joint.output, location=translate(20, 0, 0))

base.location_update(deep=True, view=False)
joint.set_coord(deg(90), view=False)
position = tip.global_location.translation()
assert abs(position.x) < 1e-7
assert abs(position.y - 20) < 1e-7

display(base)
show()
```

Геометрия рычага остаётся прежней, меняется её размещение. `global_location` учитывает всех родителей. После ручного изменения структуры или локальных положений используйте `base.location_update(deep=True)`. `view=False` подходит для расчётов без обновления отображения; при работе с показанной моделью используйте обычное обновление.

Для анимации создайте сборку до `show()`, а в callback меняйте координаты звеньев. Примеры находятся в `zencad/examples/4.Assemble`; взаимодействие с вводом описано в разделе [«Анимация»](animate.html).

## Кинематическая цепь и дерево

В самом ZenCad есть класс `kinematic_chain` из `zencad.libs.kinematic`. Это алгоритмическое представление **одного пути** в дереве сборки, а не контейнер, в который нужно повторно добавлять детали.

Конструктор `kinematic_chain(distant, proxymal=None)` идёт от конечного юнита `distant` по ссылкам `parent` к начальному `proxymal`, включая его. Если начало не указано, обход продолжается до корня. Имя аргумента `proxymal` приведено в том написании, которое используется в API; указанный юнит должен быть предком конечного.

- `getchain()` возвращает все юниты пути, включая неподвижные промежуточные.
- `kinematic_pairs` содержит только кинематические звенья; `chain[i]` обращается к этому списку.
- Порядок — **от выхода к основанию**. В таком же порядке задаются приращения и располагаются столбцы матриц для однокоординатных звеньев.

Отдельного класса `kinematic_tree` нет. Дерево задаётся связями `unit`: у одного входа или выхода может быть несколько потомков. Для каждого интересующего рабочего органа можно построить свою цепь к общему основанию. При изменении общей для ветвей координаты меняются положения всех зависимых потомков.

## Чувствительности и матрица Якоби

Цепь вычисляет локальную зависимость движения рабочего органа от изменения координат звеньев:

| Метод | Результат |
| --- | --- |
| `sensivity(basis=None)` | Список объектов `screw` с угловой частью `.ang` и линейной `.lin` |
| `sensivity_jacobian(basis=None)` | NumPy-матрица `6 × N`: угловые компоненты в первых трёх строках, линейные в последних |
| `translation_sensivity_jacobian(basis=None)` | NumPy-матрица `3 × N` линейных компонентов |
| `apply_step(increments)` | Прибавляет приращения к координатам однокоординатных звеньев |
| `apply(speeds, delta)` | Прибавляет `speed * delta` к каждой координате |

Написание `sensivity` сохранено в именах методов API. Без `basis` чувствительности выражены в системе конечного юнита; `basis=base` выражает их в системе указанного юнита. Положения дерева должны быть обновлены перед расчётом. Приращения и скорости передавайте по одному значению на каждое однокоординатное звено в порядке `kinematic_pairs`.

```python
from zencad import *
from zencad.assemble import unit, rotator, actuator
from zencad.libs.kinematic import kinematic_chain

base = unit()
hinge = rotator(axis=(0, 0, 1), parent=base)
slide = actuator(
    axis=(1, 0, 0), parent=hinge.output, location=translate(10, 0, 0)
)
tip = unit(parent=slide.output)
base.location_update(deep=True, view=False)
slide.set_coord(2, view=False)

chain = kinematic_chain(tip, proxymal=base)
assert chain.kinematic_pairs == [slide, hinge]
jacobian = chain.translation_sensivity_jacobian(basis=base)
assert jacobian.shape == (3, 2)
assert abs(jacobian[0, 0] - 1) < 1e-7
assert abs(jacobian[1, 1] - 12) < 1e-7

chain.apply_step([1, 0])
assert abs(tip.global_location.translation().x - 13) < 1e-7
```

Здесь первый столбец описывает линейный привод, второй — шарнир. При исходном вылете `12` малый поворот шарнира даёт линейную скорость по Y с коэффициентом `12`.

Есть и методы для отслеживания локальной системы внутри промежуточного юнита: `sensivity2(body, local, basis=None)`, `sensitivity_jacobian2(...)` и `translation_sensitivity_jacobian2(...)`. Они позволяют анализировать положение, отличающееся от конечной системы цепи, в том числе вход звена или юнит соседней ветви. Координаты, не влияющие на выбранный юнит, дают нулевые столбцы. `basis` меняет систему выражения абсолютной скорости; движение самого базиса из результата не вычитается.

В `zencad/examples/4.Assemble/robot-arm.py` рука из поворотных звеньев автоматически следует за красным шариком на замкнутой пространственной траектории. Линейный Якобиан и метод наименьших квадратов с демпфированием задают скорости суставов; `chain.apply()` применяет их в порядке столбцов матрицы. Пример управляет положением конца руки, не его ориентацией.


## Границы поддержки

Приведённые примеры используют `rotator` и `actuator`. В модуле есть также `planemover`, `freemover` и `spherical_rotator`, но их поддержка неоднородна: у `freemover` заявлены шесть степеней свободы, хотя установка координат реализует только перемещение по XY; `spherical_rotator.senses()` не реализован. Поэтому `freemover` и `spherical_rotator` нельзя считать готовыми заменами однокоординатных звеньев в расчёте Якоби. `planemover.set_coords([x, y])` задаёт перемещение по XY; его `senses()` возвращает линейные чувствительности по X и Y. В Якобиане цепи порядок чувствительностей внутри пары обратный: Y, затем X. `apply_step()` и `apply()` принимают только однокоординатные звенья и проверяют длину входного вектора до изменения координат.
:en
# Kinematics

Kinematics extends [assemblies](assemble.html): generalized coordinates, such as a hinge angle or actuator travel, determine part placement. Ordinary ZenCad operations build the geometry; kinematic joints control where it is placed.

## Two units per joint

A kinematic component consists of two units in relative motion:

- The joint object itself inherits `kinematic_unit` and serves as the input unit. Its `location` places the joint relative to its parent.
- `joint.output` is the output unit, parented to the input. Its placement relative to the input is determined by the joint coordinates.

```text
parent
└── joint                 input: joint mounting
    └── joint.output      output: rotation or translation
        └── payload       part or subsequent joint
```

`joint.add(shape)` attaches geometry to the input, such as an actuator housing. `joint.output.add(shape)` attaches it to the moving output. `joint.link(child)` also attaches to the **output**, whereas ordinary `unit.link(child)` attaches directly to that unit.

Use `parent=joint.output` in a child's constructor to make it follow the output. `parent=joint` attaches it to the input instead.

## Rotary and linear joints

Import these classes from `zencad.assemble`:

| Joint | Coordinate | Output motion |
| --- | --- | --- |
| `rotator(axis=...)` | `set_coord(angle)`, radians | Rotation about a local input axis |
| `actuator(axis=...)` | `set_coord(distance)`, model length units | Translation along a local input axis |

The axis is normalized. `mul` scales the coordinate: the physical angle or displacement is `coord * mul`. `location` places the input; `set_coord()` changes the output relative to it. Single-coordinate joints return `1` from `dim()` and also accept `set_coords([value])`.

A rotating arm:

```python
from zencad import *
from zencad.assemble import unit, rotator

base = unit()
joint = rotator(axis=(0, 0, 1), parent=base)
joint.add(cylinder(3, 2, center=True))
joint.output.add(box(20, 2, 2).back(1).down(1))
tip = unit(parent=joint.output, location=translate(20, 0, 0))

base.location_update(deep=True, view=False)
joint.set_coord(deg(90), view=False)
position = tip.global_location.translation()
assert abs(position.x) < 1e-7
assert abs(position.y - 20) < 1e-7

display(base)
show()
```

The arm geometry stays unchanged; its placement changes. `global_location` includes all ancestors. After manually changing the hierarchy or local placements, call `base.location_update(deep=True)`. `view=False` is useful for calculations without presentation updates; use normal updates for displayed models.

For animation, construct the assembly before `show()` and change joint coordinates in the callback. Examples live in `zencad/examples/4.Assemble`; see [Animation](animate.html) for input handling.

## Kinematic chains and trees

ZenCad itself contains `kinematic_chain` in `zencad.libs.kinematic`. It is an algorithmic view of **one path** through the assembly tree, not another container for the parts.

`kinematic_chain(distant, proxymal=None)` follows `parent` links from the terminal unit `distant` to the initial unit `proxymal`, including it. With no initial unit, it walks to the root. `proxymal` is the actual API spelling; this unit must be an ancestor of the terminal unit.

- `getchain()` returns every unit on the path, including fixed intermediate units.
- `kinematic_pairs` contains only kinematic joints; `chain[i]` indexes this list.
- Ordering runs **from the tip towards the base**. Increments and matrix columns follow this order for single-coordinate joints.

There is no separate `kinematic_tree` class. Ordinary `unit` links form the tree: an input or output can have multiple children. Construct a chain to a shared base for each end effector of interest. Changing a coordinate shared by several branches changes all dependent descendant placements.

## Sensitivities and Jacobians

A chain computes the local dependence of end-effector motion on joint coordinates:

| Method | Result |
| --- | --- |
| `sensivity(basis=None)` | A list of `screw` objects with angular `.ang` and linear `.lin` components |
| `sensivity_jacobian(basis=None)` | A `6 × N` NumPy matrix: angular components in the first three rows, linear components in the last three |
| `translation_sensivity_jacobian(basis=None)` | A `3 × N` NumPy matrix of linear components |
| `apply_step(increments)` | Adds increments to single-coordinate joints |
| `apply(speeds, delta)` | Adds `speed * delta` to each coordinate |

`sensivity` is the actual API spelling. Without `basis`, sensitivities are expressed in the terminal unit's frame; `basis=base` expresses them in that unit's frame. Update tree placements before calculating. Supply one increment or speed per single-coordinate joint in `kinematic_pairs` order.

```python
from zencad import *
from zencad.assemble import unit, rotator, actuator
from zencad.libs.kinematic import kinematic_chain

base = unit()
hinge = rotator(axis=(0, 0, 1), parent=base)
slide = actuator(
    axis=(1, 0, 0), parent=hinge.output, location=translate(10, 0, 0)
)
tip = unit(parent=slide.output)
base.location_update(deep=True, view=False)
slide.set_coord(2, view=False)

chain = kinematic_chain(tip, proxymal=base)
assert chain.kinematic_pairs == [slide, hinge]
jacobian = chain.translation_sensivity_jacobian(basis=base)
assert jacobian.shape == (3, 2)
assert abs(jacobian[0, 0] - 1) < 1e-7
assert abs(jacobian[1, 1] - 12) < 1e-7

chain.apply_step([1, 0])
assert abs(tip.global_location.translation().x - 13) < 1e-7
```

The first column describes the linear actuator; the second describes the hinge. At the initial reach of `12`, a small hinge rotation produces Y velocity with a coefficient of `12`.

To track a local frame inside an intermediate unit, use `sensivity2(body, local, basis=None)`, `sensitivity_jacobian2(...)` or `translation_sensitivity_jacobian2(...)`. These methods can analyze a frame other than the chain's terminal frame, including a joint input or a unit on a sibling branch. Coordinates that do not affect the selected unit produce zero columns. `basis` changes the frame in which absolute velocity is expressed; its own motion is not subtracted.

In `zencad/examples/4.Assemble/robot-arm.py`, a chain of rotary joints automatically follows a red ball along a closed spatial curve. The position Jacobian and damped least squares determine joint velocities; `chain.apply()` applies them in matrix-column order. The example controls the tip position, not its orientation.


## Support boundaries

The examples use `rotator` and `actuator`. The module also contains `planemover`, `freemover` and `spherical_rotator`, but support is uneven: `freemover` declares six degrees of freedom while coordinate updates only translate in XY; `spherical_rotator.senses()` is unimplemented. `freemover` and `spherical_rotator` are therefore not ready substitutes for single-coordinate joints in Jacobian calculations. `planemover.set_coords([x, y])` sets an XY translation; its `senses()` returns linear sensitivities along X and Y. The chain Jacobian reverses sensitivities within a pair: Y, then X. `apply_step()` and `apply()` accept only single-coordinate joints and validate the input vector length before changing coordinates.
::
