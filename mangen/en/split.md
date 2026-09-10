# Splitting solids: split and slice

`split` and `slice` cut a body into separate solid pieces. All material is retained: the volumes of the pieces add up to the original volume. Unlike subtraction, neither operation discards any of the resulting pieces.

The pieces stay in their original positions. To reveal the cuts, the examples below color the pieces differently and move them apart after splitting. The original body is shown in gray for comparison.

## split — divide a body using tool geometry

`split(body, tools)` divides `body` using one or more geometric tools. A tool defines a cutting boundary: it can be a planar face, such as `infplane()`, or another body. The tool itself is not added to the result; only pieces of the original body are returned.

The result is a `SplitResult`, a collection of individual `Solid` bodies. You can iterate over the pieces, access them by index, and process them independently. Their number depends on the placement of the tools.

### Two planes produce three layers

Cut a box of height 18 with horizontal planes at heights 6 and 12. This produces three layers, each 6 units thick. For the image, move the entire set to the right and add gaps between the layers.

```python
from zencad import *

body = box(30, 20, 18)
planes = [infplane().up(6), infplane().up(12)]
parts = split(body, planes)

# Arrange the three layers from bottom to top.
layers = sorted(parts, key=lambda part: float(part.center().z))
assert len(layers) == 3

# Original body on the left, separated layers on the right.
display(body, color=Color(0.7, 0.7, 0.7))
for index, part in enumerate(layers):
    display(part.translate(45, 0, index * 7),
            color=[Color(0.2, 0.6, 0.8), Color(1, 0.65, 0.2),
                   Color(0.4, 0.75, 0.4)][index])
show()
```

![Original body on the left and three separated layers on the right](../images/split-planes.png)

### Splitting with a cylinder

Here the tool is a cylinder passing all the way through a cube. The result contains two pieces: a cube with a cylindrical hole and a cylindrical core. Subtracting `body - cutter` would retain only the first piece; `split` keeps both. The ends of the tool that extend beyond the cube are not included in the result.

```python
from zencad import *

body = box(24)
cutter = cylinder(r=6, h=32).translate(12, 12, -4)
parts = split(body, cutter)

# For these dimensions, the cylindrical piece has the smaller volume.
core, remainder = sorted(parts, key=lambda part: float(part.mass()))
assert abs(float(core.mass() + remainder.mass() - body.mass())) < 1e-6

# Original body, body with a hole, and the extracted core.
display(body, color=Color(0.7, 0.7, 0.7))
display(remainder.right(36), color=Color(0.2, 0.6, 0.8))
display(core.right(64), color=Color(1, 0.65, 0.2))
show()
```

![Original cube on the left, body with a hole in the center, and cylindrical core on the right](../images/split-cylinder.png)

A tool may miss the body or merely touch its boundary. If no cut occurs, `split` returns the uncut body as the single element of its collection. For example, `split(box(2), infplane().up(3))` returns one solid with volume 8. If the input shape contains several solids, they are retained in the result. An empty set of tools raises `ValueError`; the input shape must contain solids.

## slice — divide a body with one plane

`slice` partitions a body with one plane. For a horizontal cut, specify its height: `parts = slice(body, z=8)`. Parts are ordered by their center projection along the plane normal.

The `SliceResult` is a collection of solids. A disjoint or touching plane leaves one uncut solid in the collection. For example, `len(slice(box(2), z=3)) == 1`.

With two parts, use `lower, upper = parts`. The `.lower` and `.upper` properties alias `parts[0]` and `parts[1]`; with one part, accessing `.upper` raises `IndexError` on evaluation.

### An inclined cut

Specify an arbitrary plane as `plane=(point, normal)`. This example uses the point `(0, 0, 8)` and normal `(0, -0.3, 1)`: the cutting height increases from 8 to 14 as Y increases from 0 to 20.

For an inclined plane, the normal determines the order: the negative-side piece comes first, then the positive-side piece. Reversing the normal reverses the order. Here the normal points upward, so the names `lower` and `upper` retain their usual meaning.

```python
from zencad import *

body = box(30, 20, 20)
plane = ((0, 0, 8), (0, -0.3, 1))  # Point on the plane and its normal.
lower, upper = slice(body, plane=plane)

assert abs(float(lower.mass() + upper.mass() - body.mass())) < 1e-6

# The translations only separate the pieces for display.
display(body, color=Color(0.7, 0.7, 0.7))
display(lower.right(45), color=Color(0.2, 0.6, 0.8))
display(upper.translate(45, 0, 12), color=Color(1, 0.65, 0.2))
show()
```

![Original body on the left and two pieces with inclined cut faces on the right](../images/slice-plane.png)
