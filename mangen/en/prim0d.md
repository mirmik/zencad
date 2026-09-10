# Point, vector, helper functions.

ZenCad has some math helpers and functions for working with them.

---
## Point
Some ZenCad functions use points or point arrays as parameters. You can use the `point3` function to create a point object. In addition, often a function can itself form points from a list or a tuple of coordinates.

```python
point3(0,3,6)

#Equivalent calls
interpolate([point3(0,0,0), point3(0,0,10), point3(10,0,10)])
interpolate([(0,0,0), (0,0,10), (10,0,10)])
interpolate(points([(0,0,0), (0,0,10), (10,0,10)]))
```

A point can be displayed with the display function as the corresponding vertex for such a point.

---
## Vector
Sometimes, in addition to specifying points, vector objects are used to indicate directions. The principle of working with vectors is similar to working with points.

```python
vector3(1,2,3)

interpolate(pnts=[(0,0,0), (0,0,10), (10,0,10)], tangs=[(0,0,1), (1,0,0), (0,1,0)])
```

The vector cannot be displayed directly.
Unlike a point, a vector ignores translation during transformations.

---
## Point and vector arrays
The vectors and points functions explicitly create arrays of points from arrays of coordinates.
points2 creates a two-dimensional array of points from a two-dimensional list.

```python
points([(0,0,0), (0,0,10), (10,0,10)])
vectors([(0,0,1), (1,0,0), (0,1,0)])

points2([
	[(0,0,0), (0,0,10), (10,0,10)],
	[(1,6,0), (0,5,10), (10,5,10)]
])
```

---
## Operations on points and vectors
Points and vectors can be used in mathematical operations according to the rules of linear algebra.

```python
pnt - pnt # -> vec
pnt + vec # -> pnt
vec + vec # -> vec
vec - vec # -> vec
```

---
## Empty primitive. nullshape
Empty primitive. Can participate in boolean operations.

An example of use in a loop:
```python
it = nullshape()
for i in range(7):
	it = it + box(20).translate(10*i,10*i,10*i)

#alternate: union([box(20).translate(10*i,10*i,10*i) for i in range(7)])
```

---
## Conversion of angular values. Radians and degrees
The zencad API uses radians to define angles. Using degrees requires scaling a numerical factor. This is exactly what the deg function does (synonymous with deg2rad):
`deg (180)` matches `math.pi`.

The reverse conversion is performed by the rad2deg function.

Сигнатуры:
```python
# Convert degrees to radians:
deg2rad(grad)
deg(grad)

# Convert radians to degrees:
rad2deg(rad)
```

Function code deg2rad, rad2deg:
```python
def deg2rad(grad):
    return float(grad) / 180.0 * math.pi

def rad2deg(rad):
    return float(rad) * 180.0 / math.pi
```

Пример:
```python
rotateZ(deg(45))
```

---
### Register font
Register FreeType font in system.

```python
register_font(fontpath)
```


## Domain values and evaluation

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

Ordinary `math.sin(scalar)` requests a number through `float`; `z.sin(scalar)` retains the graph dependency. Domain values are logically immutable: create a new position with an operation rather than assigning a coordinate.
