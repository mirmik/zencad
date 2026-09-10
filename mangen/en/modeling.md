# Building and splitting solids

Module functions create primitives: `box`, `sphere`, `cylinder`, `cone`, `torus`. Shapes support translation, rotation, union (`+`), difference (`-`) and intersection (`^`). `extrude` extends a planar shape; `loft`, `revol`, `pipe_shell` and `sweep` work with profiles and paths. Valid inputs depend on the operation's topology requirements.

```python
import zencad as z

outer = z.box(20, 10, 4)
hole = z.cylinder(2, 4).translate(10, 5, 0)
part = outer - hole
assert isinstance(part, z.Shape)
part.assert_valid()
```

## Split and slice

`split` partitions a body with tools and returns a collection of parts. `slice` cuts with a plane, returning lower/upper parts for a horizontal cut:

```python
import zencad as z

body = z.box(30, 20, 12)
parts = z.split(body, (z.infplane().up(4), z.infplane().up(8)))
assert len(parts) == 3
assert abs(sum(float(part.mass()) for part in parts) - 7200) < 1e-6
lower, upper = z.slice(z.box(20, center=True), z=0)
assert abs(float(lower.mass()) - 4000) < 1e-6
assert abs(float(upper.mass()) - 4000) < 1e-6
```

Use [selectors](selectors.html) for filleting/chamfering specific edges and drafting faces. Check results with [validate](validation.html), not only by looking at an image. More sweep and loft examples are in `zencad/examples/2.Operations/3.Sweep` and `zencad/examples/2.Operations/2.Operations/loft.py`.
