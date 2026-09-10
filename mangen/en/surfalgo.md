# Surface analysis

`Surface` describes a surface; `Face` is a bounded region on it. For example, the side face of a cylinder has a limited height, while its cylindrical surface extends in both directions.

## Getting a surface

`face.surface()` returns the underlying surface of a face. Use `cylinder_surface(radius)` to create a cylindrical surface around the Z axis.

```python
from zencad import *

plane = rectangle(20, 10).surface()
point = plane.point(5, 3)
normal = plane.normal(5, 3)
assert abs(float(point.z)) < 1e-7
assert normal.value() == (0, 0, 1)
```

## Parameters and normals

A point on a surface is specified by two parameters, `u` and `v`. Their meaning depends on the surface: for a cylinder, `u` is an angle in radians and `v` is height along Z.

| Method | Result |
| --- | --- |
| `surface.point(u, v)` | A `Point3` point |
| `surface.normal(u, v)` | A unit normal `Vector3` |
| `surface.u_range()`, `surface.v_range()` | Parameter ranges with `.lower` and `.upper` fields |
| `surface.u_iso(u)` | A curve at constant `u` |
| `surface.v_iso(v)` | A curve at constant `v` |

The ranges belong to the surface, not the face boundaries; they may be infinite. A `Face` also provides `face.normal(u, v)` directly. Omitting the arguments uses `u=0`, `v=0`.

## Curves on a surface

`surface.map(curve2)` maps a two-dimensional curve from parameter space `(u, v)` onto the surface and returns an `Edge`. On a cylinder, a sloping line segment in `(u, v)` becomes a helix.

The example shows the helix in orange, a generator line in green, and a circle at height 10 in blue:

```python
from zencad import *

surface = cylinder_surface(10)
uv_line = segment2(point2(0, 0), point2(deg(360), 20))
helix = surface.map(uv_line)
meridian = surface.u_iso(0).edge((0, 20))
parallel = surface.v_iso(10).edge()

display(cylinder(10, 20), color=Color(0.65, 0.75, 0.85, 0.7))
display(helix).set_color(orange, wire_color=orange)
display(meridian).set_color(green, wire_color=green)
display(parallel).set_color(blue, wire_color=blue)
show()
```

![Curves on a cylindrical surface](../images/surface-cylinder.png)

Isocurves are returned as `Curve` objects. `.edge()` creates an edge for display; for an infinite curve, specify a range, such as `.edge((0, 20))`.

A surface can also be built by [sweeping a profile along a path](sweep.html#sweep-surface).
