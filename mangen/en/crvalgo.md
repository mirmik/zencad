# Curve analysis

-------------------------
## Theory

In the parametric representation, a curve is a continuous mapping from the scalar interval _[U_min, U_max]_ to points in space.

This means that every point _P_ on the curve has a corresponding scalar parameter _U_.
The length of a curve segment generally differs from the difference between its endpoint parameters.

This section describes methods relating curve parameters to points and lengths.

-----------------
## Curve classes
ZenCad provides curve analysis methods in the following classes:

* Edge (created by segment, interpolate, bezier, bspline, etc.);
* Curve;
* Curve2.

---
## Endpoints and parameter range
Finding the endpoints of finite curves.

The _endpoints_ method returns the endpoint objects.
The _range_ method returns their parameters.

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
## `curve.d0(u)`
Returns the point at parameter _u_.

---------------
## `curve.d1(u)`
Returns the first derivative vector at parameter _u_.

## `curve.lower_distance_parameter(pnt)`
Returns the parameter of the point on the curve closest to `pnt`.

-------------------------------------------
## Equally spaced points
Returns an array of points equally spaced along the curve. The _npnts_ parameter sets the number of points.
It must be an integer of at least two. Specify both range boundaries or omit both; the result includes the endpoints. Spacing is measured along the curve, rather than in parameter space.
The `umin` and `umax` parameters define the parameter range to distribute the points over.

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

`Curve2` has its own interface: `point(u)` returns a `Point2`, `tangent(u)` returns a `Vector2` of the first derivative, and `range()` returns an `Interval`. Use `trim(start, end)` to restrict the range. The `d0`, `d1`, `endpoints` and `uniform_points` methods described above for `Edge` and `Curve` are not part of the `Curve2` interface.

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
