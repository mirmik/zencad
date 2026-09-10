# Affine transformations

In _ZenCad_, most objects are created at the origin, then moved into place using transformations.

Geometry is usually transformed through methods of _Shape_, the class representing geometric shapes. For complex transformations or animation, affine transformations can also be created as standalone objects.

`Transform` describes translation, rotation and uniform scaling, including reflections through signed scale; `AffineTransform` provides general affine transformations.

General transformations are more computationally expensive and may substantially change an object's internal geometric representation.

Transformations can be composed and inverted; see “Operations on transformations”.

Transformation utilities and special transformations are described under “Additional transformations”.

----------------------------------------------------
## Basic transformations
There are four basic transformations: rotation, translation, scaling and reflection.

----------------------------------------
### Rotation
Rotates a shape by angle _a_ around an axis defined by vector _v_ and passing through the origin.

If _a_ is omitted, the rotation angle in radians equals the magnitude of _v_.

Methods of transformable geometric objects:
```python
# Main syntax:
shp.rotate([x,y,z], angle)
shp.rotate([x,y,z])
shp.rotateX(x)
shp.rotateY(y)
shp.rotateZ(z)

# Shorthand syntax:
shp.rot([x,y,z], angle)
shp.rot([x,y,z])
shp.rotX(x)
shp.rotY(y)
shp.rotZ(z)
```
Creating a transformation object:
```python
rotate([x,y,z], angle)
rotate([x,y,z])
rotateX(x)
rotateY(y)
rotateZ(z)
```

-----------------------------------------
### Translation
Translates a shape by vector _(x, y, z)_.
For historical reasons, including OpenSCAD compatibility, ZenCad provides two synonymous families of functions and methods, `translate` and `move`, as well as mnemonic names.

Methods of transformable geometric objects:
```python
# Main, alternative and mnemonic syntax:
shp.translate(x,y,z)
shp.translate([x,y,z])
shp.move(x,y,z)
shp.move([x,y,z])
shp.moveX(x)
shp.moveY(y)
shp.moveZ(z)
shp.right(x) # moveX(+x)
shp.left(x)  # moveX(-x)
shp.forw(y)  # moveY(+y)
shp.back(y)  # moveY(-y)
shp.up(z)    # moveZ(+z)
shp.down(z)  # moveZ(-z)

# Shorthand syntax:
shp.movX(x)
shp.movY(y)
shp.movZ(z)
```

Creating a transformation object:
```python
# Main syntax:
translate(x,y,z)
translate([x,y,z])

# Alternative syntax:
move(x,y,z)
move([x,y,z])
moveX(x)
moveY(y)
moveZ(z)

# Mnemonic syntax:
right(x) # moveX(+x)
left(x)  # moveX(-x)
forw(y)  # moveY(+y)
back(y)  # moveY(-y)
up(z)    # moveZ(+z)
down(z)  # moveZ(-z)
```

-------------------------------
### Scaling
Scales a shape by a factor of _a_, either along an axis or uniformly.

Methods of transformable geometric objects:
```python
shp.scale(a)
shp.scaleX(a)
shp.scaleY(a)
shp.scaleZ(a)
```

Creating a transformation object:
```python
scale(a)
scaleX(a) # general_transformation
scaleY(a) # general_transformation
scaleZ(a) # general_transformation
scaleXYZ(x,y,z) # general_transformation
```

----------------------------------
### Reflection
Reflects geometry about a point, an axis through the origin, or a plane through the origin.

For reflection about a point, specify the center coordinates.
For reflection about an axis, specify its direction vector.
For reflection about a plane, specify its normal vector.

Methods of transformable geometric objects:
```python
# Reflection about a point.
shp.transform(mirrorO(x,y,z))
shp.transform(mirrorO([x,y,z]))

# Reflection about an axis.
shp.transform(mirror_axis(x,y,z))
shp.transform(mirror_axis([x,y,z]))
shp.mirrorX() # equal to mirror_axis(1,0,0)
shp.mirrorY() # equal to mirror_axis(0,1,0)
shp.mirrorZ() # equal to mirror_axis(0,0,1)

# Reflection about a plane.
shp.transform(mirror_plane(x,y,z))
shp.transform(mirror_plane([x,y,z]))
shp.mirrorXY() # equal to mirror_plane(0,0,1)
shp.mirrorYZ() # equal to mirror_plane(1,0,0)
shp.mirrorXZ() # equal to mirror_plane(0,1,0)
```

Creating a transformation object:
```python
# Reflection about a point.
mirrorO(x,y,z)
mirrorO([x,y,z])

# Reflection about an axis.
mirror_axis(x,y,z)
mirror_axis([x,y,z])
mirrorX() # equal to mirror_axis(1,0,0)
mirrorY() # equal to mirror_axis(0,1,0)
mirrorZ() # equal to mirror_axis(0,0,1)

# Reflection about a plane.
mirror_plane(x,y,z)
mirror_plane([x,y,z])
mirrorXY() # equal to mirror_plane(0,0,1)
mirrorYZ() # equal to mirror_plane(1,0,0)
mirrorXZ() # equal to mirror_plane(0,1,0)
```

-----
## Operations on transformations

An affine transformation has the form `p → A·p + t`. With nonzero translation, it is not a linear operator on three-dimensional vectors; composition can be represented using 4 × 4 matrices in homogeneous coordinates.

---------------
### Composition
Use multiplication to compose affine transformations.
Composition is not commutative.

Read compositions from right to left. In `moveX(20) * rotateZ(deg(60))`, the 60-degree rotation is applied first, followed by a translation of 20 units along X.

Example:
```python
trans = moveX(20) * rotateZ(deg(60))
from zencad.internal_models import knight
m = knight()
disp(trans(m))

# alternate: box(5, center=True).rotZ(deg(60)).movX(20)
```

| Before | After |
|---|---|
| ![complextrans0](../images/generic/complextrans0.png) | ![complextrans1](../images/generic/complextrans1.png) |

-----
### Inversion
Computes the inverse transformation.

Signature:
```python
trsf.inverse()
```

Example:
```python
trans = rotateZ(deg(45))
from zencad.internal_models import knight
m = knight()
disp(trans(m), color.green)
disp(trans.inverse()(m), color.red)
```
| Transformation | Inverse |
|---|---|
| ![invtrans0](../images/generic/invtrans2.png) | ![invtrans1](../images/generic/invtrans3.png) |

Example:
```python
trans = moveX(20) * rotateZ(deg(45))
from zencad.internal_models import knight
m = knight()
disp(trans(m), color.green)
disp(trans.inverse()(m), color.red)
```
| Transformation | Inverse |
|---|---|
| ![invtrans0](../images/generic/invtrans0.png) | ![invtrans1](../images/generic/invtrans1.png) |

Note. The inverse of a composition can be computed as:
_<p align=center>(A * B)<sup>-1</sup> = B<sup>-1</sup> * A<sup>-1</sup><p/>_

----
## Additional transformations

-----------------------------------
### Identity transformation
Leaves the object unchanged. Create it with `transform()` or `nulltrans()`.

```python
nulltrans()
```

| Before | After |
|---|---|
| ![nulltrans0](../images/generic/nulltrans01.png) | ![nulltrans0](../images/generic/nulltrans01.png) |

---------
### Shortest rotation
The shortest rotation from vector _<span style="color:green">f</span>_ to vector _<span style="color:blue">t</span>_.

Signature:
```python
short_rotate(f, t)
```

Example:
```python
from zencad.internal_models import knight
short_rotate((0,0,1), (1,1,1))(knight())
```

| Before | After |
|---|---|
| ![multitrans0](../images/generic/short_rotate0.png) | ![multitrans0](../images/generic/short_rotate1.png) |

------------------------------------
### Multiple transformations
Applies an array of transformations, `transes`, to a prototype.
With _array_ disabled, the results are combined by Boolean union. With _array_ enabled, an array of results is returned.

Create an assembly explicitly: `unit(parts=copies)`, after importing `unit` from `zencad.assemble`.

Signature:
```python
copies = multitrans(transes, array=True)(model)
fused = multitrans(transes)(model)
# multitransform is a synonym for multitrans
```

Example:
```python
def extrans():
    return multitransform([
        translate(-20,20,0) * rotateZ(deg(60)),
    translate(-20,-20,0) * rotateZ(deg(120)),
    translate(20,20,0) * rotateZ(deg(180)),
    nulltrans()
])
from zencad.internal_models import knight
disp(extrans()(knight()))
```

| Before | After |
|---|---|
| ![multitrans0](../images/generic/multitrans0.png) | ![multitrans0](../images/generic/multitrans1.png) |

----------
### Circular array
Creates a circular array of _n_ objects over the angular range _yaw_. The _endpoint_ parameter controls whether the final angle is included.
(For _array_, see Multiple transformations.)

Signature and transformation code:
```python
rotate_array(n, yaw=deg(360), endpoint=False, array=False)
```
Examples:
```python
from zencad.internal_models import knight
m = knight().move(20,20)
disp(rotate_array(6, yaw=deg(270), endpoint=True)(m))
```
| Before | After |
|---|---|
| ![ra0](../images/generic/rotate_array0.png) | ![ra1](../images/generic/rotate_array1.png) |

----------
### Circular array with roll
Creates a circular array of _n_ objects over the angular range _yaw_. The _endpoint_ parameter controls whether the final angle is included.
(For _array_, see Multiple transformations.)

The _roll_ option sets the range of roll angles around the circular path.

`rotate_array2` positions the source object differently from _rotate_array_: the source starts at the origin, is rotated by 90 degrees around X, then translated along X by the radius _r_.

Signature:
```python
rotate_array2(
	n, r=None,
	yaw=(0,deg(360)), roll=(0,0),
	endpoint=False, array=False)
```
Example:
```python
rotate_array2(
	n=60,
	r=20,
	yaw=(0,deg(270)),
	roll=(0,deg(360)),
	array=True)(
		square(10, center=True, wire=True)
	)
```
| Before | After |
|---|---|
| ![raa0](../images/generic/rotate_array20.png) | ![ra1](../images/generic/rotate_array21.png) |

### Square reflection
Adds three reflections of the source object.

Signature and transformation code:
```python
sqrmirror(array=False)
sqrtrans(array=False) # synonym
```

Example:
```python
from zencad.internal_models import knight
sqrmirror()(knight().move(20,30))
```

| Before | After |
|---|---|
| ![ra0](../images/generic/sqrmirror0.png) | ![ra1](../images/generic/sqrmirror1.png) |

## Transforming a point and obtaining a matrix

A transformation object can be applied to a point. `Transform.matrix()` returns a numeric 4×4 matrix, evaluating the required dependencies.

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

## Quaternions

`quaternion(x, y, z, w)` defines a quaternion with the scalar component `w` last. `quaternion(0, 0, 0, 1)` represents no rotation. To specify an axis and angle, use `quaternion_axis_angle`:

```python
from zencad import *

q = quaternion_axis_angle(vector3(0, 0, 1), deg(90))
v = q.rotate(vector3(1, 0, 0))
assert abs(float(v.x)) < 1e-7
assert abs(float(v.y) - 1) < 1e-7
placement = q.to_transform()
display(placement(box(10, 5, 3)))
show()
```

`q1 * q2` composes rotations from right to left; `q.inverse()` returns the inverse rotation. `q.normalized()` normalizes the quaternion, and `q.to_transform()` converts it to a `Transform`.
