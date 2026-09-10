# Geometric properties
This section covers measuring the geometric properties of a model.

Geometry calculations use model units: volume is measured in cubic units. STL/STEP/3MF exporters interpret source coordinates as millimetres. To obtain physical mass, multiply volume by density in matching units.

----------------------------------------
## Built-in methods
Shape provides methods for querying geometric information.

----
### Center of mass
```python
shape.center() # -> Point3
```

----
### Volume
```python
shape.mass() # -> Scalar
```

## Example

For a solid, `mass()` returns volume as a `Scalar`; `center()` returns the center of mass as a `Point3`. `.value()` obtains a number or coordinate tuple.

```python
import zencad as z

body = z.box(2, 3, 4)
volume = body.mass()
center = body.center()
assert abs(volume.value() - 24) < 1e-7
assert all(abs(a - b) < 1e-7 for a, b in zip(center.value(), (1, 1.5, 2)))
```

Use [inspect](headless.html) for area and aggregate properties of the visible scene, and the [bounding box](bbox.html) for dimensions.
