# Values, points and transforms

`scalar`, `point2`, `point3`, `vector2`, `vector3`, `quaternion` and `transform` construct numbers, points, vectors, quaternions and transforms. Their result types are `Scalar`, `Point2`, `Point3`, `Vector2`, `Vector3`, `Quaternion` and `Transform`, respectively. Geometry and numeric dependencies remain in the graph until explicitly requested.

```python
import zencad as z

p = z.point3(1, 2, 3)
v = z.vector3(4, 0, 0)
q = p + v
assert q.value() == (5, 2, 3)
assert isinstance(q - p, z.Vector3)
assert isinstance(v + v, z.Vector3)
coordinates = q.to_numpy()
assert coordinates.shape == (3,)
body = z.box(2)
volume = body.mass()
assert isinstance(volume, z.Scalar)
assert abs(volume.value() - 8) < 1e-7
assert isinstance(body.center().x, z.Scalar)
```

Coordinates accept numbers, and supported operations accept dependent `Scalar` values. `Point + Point` is invalid. Scaling a vector produces a vector; translation affects a point but not a direction.

```python
import zencad as z

number = z.scalar(2)
p2 = z.point2(1, 2)
p3 = z.point3(1, 2, 3)
v2 = z.vector2(1, 0)
v3 = z.vector3(0, 0, 1)
rotation = z.quaternion(0, 0, 0, 1)
placement = z.transform()
assert placement(p3).value() == p3.value()
```

## Materialization boundaries

- `Scalar.value()`, `float()`, `int()`, `bool()` and comparisons require a number.
- `Point/Vector.value()` returns a tuple; `.to_numpy()` returns a numeric array.
- `Shape.native()` returns an OCP shape; `Point/Vector.to_ocp()` returns a native point/vector.
- `Transform.matrix()` returns a numeric 4×4 matrix.

Ordinary `math.sin(scalar)` requests a number through `float`; `z.sin(scalar)` retains the graph dependency. Domain values are logically immutable: create a new position with an operation rather than assigning a coordinate.

## Transforms

```python
import zencad as z

move = z.translate(10, 0, 0)
turn = z.rotateZ(z.deg(90))
combined = move * turn
p = combined(z.point3(1, 0, 0))
assert abs(float(p.x) - 10) < 1e-7
assert abs(float(p.y) - 1) < 1e-7
matrix = combined.matrix()
```

`outer * inner` applies `inner` first, then `outer`. `Transform` represents translation, rotation and uniform scale, including reflections through signed scale; general affine transformations use `AffineTransform`. [Topology selectors](selectors.html).
