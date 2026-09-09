:ru
# Геометрические характеристики

Запросы геометрии возвращают доменные значения; используйте `.value()` для чисел Python. Для solid `mass()` измеряет объём при единичной плотности, а не физическую массу материала.

```python
import zencad as z

body = z.box(2, 3, 4)
volume = body.mass()
center = body.center()
assert abs(volume.value() - 24) < 1e-7
assert all(abs(a - b) < 1e-7 for a, b in zip(center.value(), (1, 1.5, 2)))
```

Для площади и агрегированных свойств видимой сцены используйте [inspect](headless.html). [Bounding box](bbox.html) и [топология](selectors.html) сохраняют зависимости в графе. Физическую массу вычисляйте отдельно из объёма, единиц и плотности материала.
:en
# Geometric properties

Geometry queries return domain values; use `.value()` for Python numbers. On a solid, `mass()` measures volume at unit density, not physical material mass.

```python
import zencad as z

body = z.box(2, 3, 4)
volume = body.mass()
center = body.center()
assert abs(volume.value() - 24) < 1e-7
assert all(abs(a - b) < 1e-7 for a, b in zip(center.value(), (1, 1.5, 2)))
```

Use [inspect](headless.html) for area and aggregate properties of the visible scene. [Bounding boxes](bbox.html) and [topology](selectors.html) retain graph dependencies. Compute physical mass separately from volume, units and material density.
::
