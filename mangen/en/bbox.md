# Bounding box

A bounding box is a box aligned with the X, Y and Z axes that encloses a geometric shape.

---
## shape.bbox
Build a bounding box for a shape.

Example:
```python
shp = sphere(10)
bbox = shp.bbox()
```

## Fields
```python3
bbox.xmin
bbox.ymin
bbox.zmin
bbox.xmax
bbox.ymax
bbox.zmax
```

## Methods
`bbox.xrange()`, `bbox.yrange()` and `bbox.zrange()` return coordinate ranges.

## Creating a box shape
Example:
```python
shp = sphere(10)
bbox = shp.bbox()
disp(bbox.shape())
```

## Dimensions and coordinates

`shape.boundbox()` and `shape.bbox()` return an axis-aligned `BoundaryBox`. Coordinates are `Scalar` values; `minimum`, `maximum` and `center` are `Point3`; `size` is `Vector3`.

```python
import zencad as z

bounds = z.box(2, 3, 4).bbox()
assert all(abs(a - b) < 1e-5 for a, b in zip(bounds.size.value(), (2, 3, 4)))
record = bounds.value()
print(record.minimum, record.maximum)
```

`xmin`, `xmax`, `ymin`, `ymax`, `zmin` and `zmax` are properties; `xlength()`, `ylength()` and `zlength()` are methods. `.value()` returns numerical bounds; `.native()` returns an OCP `Bnd_Box`. OCCT tolerances may slightly enlarge the bounds, so compare dimensions with a tolerance. Empty geometry needs separate handling; do not assume it has a zero-sized box.
