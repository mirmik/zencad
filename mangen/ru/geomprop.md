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
