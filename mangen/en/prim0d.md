# Points, vectors and utilities

## Points

`point3(x, y, z)` creates a three-dimensional point; `point2(x, y)` creates a two-dimensional point. Most geometry functions also accept coordinate tuples.

```python
from zencad import *

p = point3(1, 2, 3)
assert p.value() == (1, 2, 3)
assert float(p.x) == 1

curve = interpolate([(0, 0, 0), (0, 0, 10), (10, 0, 10)])
display(curve)
display(p)
show()
```

A point is displayed as a vertex. Both rotation and translation apply when transforming it.

## Vectors

`vector3(x, y, z)` and `vector2(x, y)` describe directions and displacements. Translation does not affect a vector. Use an [arrow](interactive_object.html) to display one.

| Operation | Result |
| --- | --- |
| `p - q` | A vector between points |
| `p + v`, `p - v` | A displaced point |
| `v + w`, `v - w`, `v * k` | A vector |
| `v.length()` | Length |
| `v.normalized()` | A unit vector in the same direction |
| `v.dot(w)` | Dot product |
| `v.cross(w)` | Cross product; for `Vector2`, its scalar Z component |

Adding two points is not allowed. Operations create new values without changing the original coordinates.

```python
from zencad import *

v = vector3(3, 4, 0)
assert float(v.length()) == 5
assert abs(float(v.normalized().length()) - 1) < 1e-7
assert vector3(1, 0, 0).cross(vector3(0, 1, 0)).value() == (0, 0, 1)
```

## Arrays of points and vectors

`points` and `vectors` create lists of three-dimensional points and vectors. `points2` creates a two-dimensional grid of three-dimensional points, for example for surface interpolation.

```python
points([(0, 0, 0), (0, 0, 10), (10, 0, 10)])
vectors([(0, 0, 1), (1, 0, 0), (0, 1, 0)])
points2([
    [(0, 0, 0), (10, 0, 5)],
    [(0, 10, 0), (10, 10, 5)],
])
```

## Numbers and evaluation

The functions `point3`, `vector3` and `scalar` return `Point3`, `Vector3` and `Scalar` objects. These preserve computation dependencies. `.value()` returns a number or coordinate tuple; `.to_numpy()` on a point or vector returns a NumPy array.

```python
from zencad import *

body = box(2)
volume = body.mass()             # Scalar
moved = body.right(volume / 4)   # Translation depends on volume.
assert abs(float(volume) - 8) < 1e-7
coordinates = moved.center().to_numpy()
```

`float`, `int`, `bool` and comparisons request a numerical result. `math.sin(value)` also evaluates a number; ZenCad's `sin(value)` preserves the dependency. See [Evaluation and caching](caching.html).

## Radians and degrees

Angles in the ZenCad API use radians. `deg(180)` equals `math.pi`; `deg2rad` is an alias for `deg`, and `rad2deg` performs the reverse conversion.

```python
rotateZ(deg(45))
```

## Empty primitive: nullshape

An empty shape can take part in boolean operations:

```python
it = nullshape()
for i in range(7):
    it = it + box(20).translate(10*i, 10*i, 10*i)

# The same using a list:
# union([box(20).translate(10*i, 10*i, 10*i) for i in range(7)])
```

## Registering a font

`register_font(fontpath)` registers a FreeType font for creating [text](prim2d.html).
