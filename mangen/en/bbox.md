# Bounding box

The bounding box is a minimal Ox, Oy, Oz-based box that describes the geometric shape shape.

---
## shape.bbox
Construct a bounding box based on the shape.

Пример
```python
shp = sphere(10)
bbox = shp.bbox()
```

## Fields.
```python3
bbox.xmin
bbox.ymin
bbox.zmin
bbox.xmax
bbox.ymax
bbox.zmax
```

## Methods.
bbox.xrange()
bbox.yrange()
bbox.zrange()

## To Shape.
Пример
```python
shp = sphere(10)
bbox = shp.bbox()
disp(bbox.shape())
```


## Domain values and evaluation

`shape.boundbox()` and `shape.bbox()` return an axis-aligned `BoundaryBox`. Coordinates are `Scalar`; `minimum`/`maximum`/`center` are `Point3`; `size` is `Vector3`.

```python
import zencad as z

bounds = z.box(2, 3, 4).bbox()
assert all(abs(a - b) < 1e-5 for a, b in zip(bounds.size.value(), (2, 3, 4)))
record = bounds.value()
print(record.minimum, record.maximum)
```

`xmin`, `xmax`, `ymin`, `ymax`, `zmin`, `zmax` are properties; `xlength()`/`ylength()`/`zlength()` are methods. `.value()` returns a materialized record; `.native()` returns `Bnd_Box`. OCCT tolerances may slightly enlarge bounds, so compare dimensions with tolerance. Empty geometry needs explicit handling, rather than assuming a zero-sized box.
