# Проверка и исправление геометрии

## Проверка: validate и assert_valid

`validate()` возвращает отчёт об ошибках, `is_valid()` — признак корректности. `assert_valid()` выбрасывает `ShapeValidationError`, если форма некорректна. Эти методы ничего не исправляют.

```python
import zencad as z

body = z.box(10)
report = body.validate()
assert report.valid
print(report.to_dict())
body.assert_valid()
```

Валидность не означает замкнутость тела. Для проверки итогового solid используйте `zencad check model.py --valid --solid`. [Формат отчёта](../development/shape-validation.md).

## unify

Удаляет лишние рёбра и объединяет грани одной поверхности. Работает с двумерными и трёхмерными объектами. Для такого упрощения также доступен метод `body.clean()`.

```python
from zencad import *

body = cylinder(r=10, h=10) + cylinder(r=10, h=10).move(5, 5)
simplified = unify(body)
simplified.assert_valid()
display(simplified)
show()
```

| До | После |
|---|---|
| ![](../images/generic/unify0.png) | ![](../images/generic/unify1.png) |

## heal — исправление дефектов геометрии

Исправляет дефекты средствами OpenCascade, создавая новую форму. Результат нужно проверить: исправление не всегда возможно.

В примере ([box-reversed-face.brep](../files/box-reversed-face.brep)) — куб 10 × 10 × 10 с неправильно ориентированной гранью.

```python
from pathlib import Path
import zencad as z

body = z.from_brep(Path(__file__).with_name("box-reversed-face.brep"))
before = body.validate()
print(before.valid)  # False
print([issue.code for issue in before.issues])
# ['bad_orientation_of_subshape']

fixed = body.heal(tolerance=1e-7, max_tolerance=1e-3)
fixed.assert_valid()
print(fixed.is_valid())  # True
print(round(float(fixed.mass()), 6))  # 1000.0

assert not body.is_valid()
z.display(fixed)
z.show()
```

`heal` исправляет ориентацию грани; исходная форма остаётся неизменной. `tolerance` задаёт рабочую точность, `max_tolerance` — верхнюю границу допуска, в единицах модели.
