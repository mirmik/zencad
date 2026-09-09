:ru
# Ограничивающая коробка

`shape.boundbox()` и `shape.bbox()` возвращают `BoundaryBox`, выровненную по осям. Координаты — `Scalar`, `minimum`/`maximum`/`center` — `Point3`, `size` — `Vector3`.

```python
import zencad as z

bounds = z.box(2, 3, 4).bbox()
assert all(abs(a - b) < 1e-5 for a, b in zip(bounds.size.value(), (2, 3, 4)))
record = bounds.value()
print(record.minimum, record.maximum)
```

`xmin`, `xmax`, `ymin`, `ymax`, `zmin`, `zmax` — свойства, `xlength()`/`ylength()`/`zlength()` — методы. `.value()` возвращает материализованную запись; `.native()` — `Bnd_Box`. Допуски OCCT могут немного расширять границы, поэтому сравнивайте размеры с допуском. Пустая геометрия требует отдельной обработки, не предполагает нулевую коробку.
:en
# Bounding boxes

`shape.boundbox()` and `shape.bbox()` return an axis-aligned `BoundaryBox`. Coordinates are `Scalar`; `minimum`/`maximum`/`center` are `Point3`; `size` is `Vector3`.

```python
import zencad as z

bounds = z.box(2, 3, 4).bbox()
assert all(abs(a - b) < 1e-5 for a, b in zip(bounds.size.value(), (2, 3, 4)))
record = bounds.value()
print(record.minimum, record.maximum)
```

`xmin`, `xmax`, `ymin`, `ymax`, `zmin`, `zmax` are properties; `xlength()`/`ylength()`/`zlength()` are methods. `.value()` returns a materialized record; `.native()` returns `Bnd_Box`. OCCT tolerances may slightly enlarge bounds, so compare dimensions with tolerance. Empty geometry needs explicit handling, rather than assuming a zero-sized box.
::
