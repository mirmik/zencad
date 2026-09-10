# Geometric characteristics.
The section is devoted to measuring the geometric characteristics of the constructed geometry.

Since the concepts of density and scale are very ephemeral for the computational library, all calculations are carried out in arbitrary units. Converting values to the si system requires additional calculations.

----------------------------------------
## Built-in methods
Shape has a number of methods for querying geometric information.

----
### Center of mass.
```python
shape.center() # -> Point3
```

----
### Volume.
```python
shape.mass() # -> Scalar
```



## Domain values and evaluation

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
