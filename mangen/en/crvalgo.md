# Curve analysis 

-------------------------
## Theoretical summary.
The generally accepted method for defining curves in computational geometry systems is the parametric method.

According to him, the curve is given by a continuous mapping of the scalar set _[U \_min, U \_max]_ onto a space of a given dimension.
_P = F (U): P ∈ R ^ N, U ∈ R ^ 1 [U \_min, U \_max]_, where _F_ is the mapping functor and _N_ is the dimension of the space.

In practice, this means that any point _P_ on the curve has a corresponding value of the scalar parameter _U_. It should be understood that, in the general case, the function connecting the parameter _U_ at the point _P_ and the length of the curve from the start point _O_ to the point _P_ is not linear. Therefore, calculations over a curve in terms of lengths require the use of a special mathematical apparatus (implemented in the form of methods in this library). 

-----------------
## Classes of curves.
ZenCad has the following classes that implement curve analysis methods:

* Edge (spawned by segment, interpolate, bezier, bspline, etc.)
* Curve
* Curve2 

---
## End points and end curve range.
Determines the endpoints of the end curves.

The _endpoints_ method returns endpoint objects.
The parameters of these points can be queried using the _range_ method. 

```python 
curve.endpoints() # -> tuple[Point3, Point3]
curve.range() # -> Interval; .lower/.upper -> Scalar
```

```python
crv = circle(r=5, wire=True, angle=deg(270))
s,f = crv.endpoints()
disp([crv, s, f])
```
![](../images/generic/endpoints0.png)

--------------
## curve.d0 (u)
Return the point corresponding to the _u_ parameter. 

---------------
## curve.d1 (u)
Return the vector of the first derivative matching the _u_ parameter. 

## curve.lower_distance_parameter(pnt)
Return the parameter corresponding to the point on the curve closest to the point pnt. 

-------------------------------------------
## Equidistant curve points.
Return an array of points equally spaced along the curve. The _npnts_ parameter sets the number of points.
The count must be an integer of at least two. Supply both range bounds together or omit both; the endpoints are included. Spacing is uniform along arc length, not in parameter values.
The parameters umin, umax set the range on the set of parameters in which the distribution procedure will be carried out. 

```python3
curve.uniform(npnts, U_min, U_max) # -> list[Scalar]
curve.uniform_points(npnts, U_min, U_max) # -> list[Point3]
```  

```python
crv = circle(r=5, wire=True, angle=deg(270))

params = crv.uniform(8, math.pi/4, math.pi)
print([float(p) for p in params]) # [0.7853981633974483, 1.121997376282069, 1.4585965891666897, 1.7951958020513104, 2.131795014935931, 2.4683942278205517, 2.8049934407051724, 3.141592653589793]

pnts = crv.uniform_points(8, math.pi/4, math.pi)
disp(pnts + [crv])
```

![](../images/generic/uniform_points0.png)

## Two-dimensional curves

`Curve2` has its own interface: `point(u)` returns `Point2`, `tangent(u)` returns the first derivative as `Vector2`, and `range()` returns `Interval`. Use `trim(start, end)` to restrict its domain. The `d0`, `d1`, `endpoints`, and `uniform_points` methods described above for `Edge` and `Curve` are not part of the `Curve2` interface.

```python
from zencad import *

curve2 = segment2(point2(0, 0), point2(10, 0))
interval = curve2.range()
start = curve2.point(interval.lower)
end = curve2.point(interval.upper)
assert float(start.x) == 0
assert float(end.x) == 10
assert isinstance(curve2.tangent(interval.lower), Vector2)
```
