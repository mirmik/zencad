# Ограничивающая коробка

Ограничивающая коробка - это это минимальный основанный на осях Ox, Oy, Oz параллелепипед, описывающий геометрическую форму shape.

---
## shape.bbox
Построить ограничивающую коробку на основе формы shape.

Пример
```python
shp = sphere(10)
bbox = shp.bbox()
```

## Поля.
```python3
bbox.xmin
bbox.ymin
bbox.zmin
bbox.xmax
bbox.ymax
bbox.zmax
```

## Методы.
bbox.xrange()
bbox.yrange()
bbox.zrange()

## Построить коробку как форму.
Пример
```python
shp = sphere(10)
bbox = shp.bbox()
disp(bbox.shape())
```


## Доменные значения и вычисления

`shape.boundbox()` и `shape.bbox()` возвращают `BoundaryBox`, выровненную по осям. Координаты — `Scalar`, `minimum`/`maximum`/`center` — `Point3`, `size` — `Vector3`.

```python
import zencad as z

bounds = z.box(2, 3, 4).bbox()
assert all(abs(a - b) < 1e-5 for a, b in zip(bounds.size.value(), (2, 3, 4)))
record = bounds.value()
print(record.minimum, record.maximum)
```

`xmin`, `xmax`, `ymin`, `ymax`, `zmin`, `zmax` — свойства, `xlength()`/`ylength()`/`zlength()` — методы. `.value()` возвращает материализованную запись; `.native()` — `Bnd_Box`. Допуски OCCT могут немного расширять границы, поэтому сравнивайте размеры с допуском. Пустая геометрия требует отдельной обработки, не предполагает нулевую коробку.
