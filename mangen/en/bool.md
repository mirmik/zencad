# Boolean operations

CSG geometry relies on Boolean operations. ZenCad provides union, difference and intersection for 3D and 2D objects, in two forms:

* functions _union_, _difference_ and _intersect_ for arrays of shapes;
* operators _+_, _-_ and _^_ for pairs of shapes.

>! Note:
>! To join simple curves into a composite wire or sew faces into a shell, use the dedicated stitching operations described in the corresponding sections.

---
## Union

Signature:
```python
# Function:
result = union(array)

# Operator:
result = shp0 + shp1
```

Example:
```python
#with operators:
sphere(r=10) + cylinder(r=5, h=10, center=True) + cylinder(r=5, h=10, center=True).rotateX(deg(90))

#with function:
union([
	sphere(r=10), 
	cylinder(r=5, h=10, center=True), 
	cylinder(r=5, h=10, center=True).rotateX(deg(90))
])
```
![](../images/generic/union.png) ![](../images/generic/union0.png) </br>
![](../images/generic/union1.png) ![](../images/generic/union2.png)

---
## Difference
Signature:
```python
# Function:
result = difference(array)

# Operator:
result = shp0 - shp1
```

Example:
```python
#with operators:
sphere(r=10) - cylinder(r=5, h=10, center=True) - cylinder(r=5, h=10, center=True).rotateX(deg(90))

#with function:
difference([
	sphere(r=10), 
	cylinder(r=5, h=10, center=True), 
	cylinder(r=5, h=10, center=True).rotateX(deg(90))
])
```
![](../images/generic/difference.png) ![](../images/generic/difference0.png) </br>
![](../images/generic/difference1.png) ![](../images/generic/difference2.png)

---
## Intersection

Signature:
```python
# Function:
result = intersect(array)

# Operator:
result = shp0 ^ shp1
```

Example:
```python
#with operators:
sphere(r=10) ^ cylinder(r=5, h=10, center=True) ^ cylinder(r=5, h=10, center=True).rotateX(deg(90))

#with function:
intersect([
	sphere(r=10), 
	cylinder(r=5, h=10, center=True), 
	cylinder(r=5, h=10, center=True).rotateX(deg(90))
])
```
![](../images/generic/intersect.png) ![](../images/generic/intersect0.png) </br>
![](../images/generic/intersect1.png) ![](../images/generic/intersect2.png)

---
## Shell intersection
A relative of _intersect_ that computes the intersection of the solids' shells.

Signature:
```python
# Function:
result = section(a, b)
```

Example:
```python
m0 = section(box(10, center=True) - sphere(4))
m1 = section(box(10, center=True), sphere(7))

```
![](../images/generic/section0.png)
![](../images/generic/section1.png)

---
## Splitting and slicing with a plane

`split(body, tools)` splits a solid with Shape tools; `slice(body, z=..., axis=...)` uses a single plane. Both return collections of solid parts and preserve uncut solids. An empty tool collection for `split` raises `ValueError`.

`slice` orders its parts along the plane normal. A two-part result can be unpacked as `lower, upper`. See [Splitting solids](split.html) for details and examples.

```python
parts = split(box(10), (infplane().up(3), infplane().up(7)))

lower, upper = slice(box(10), z=4)
left, right = slice(box(10), z=2, axis="x")
negative, positive = slice(box(10), plane=((0, 5, 0), (0, 1, 0)))
```

---------------------------------------------
## Boolean operations on 2D shapes
The same operations apply to two-dimensional objects as long as they lie in the same plane.

Example:
```python
m0 = circle(10) - square(10)
m1 = circle(10) + square(10)
m2 = circle(10) ^ square(10)
m3 = section(circle(10), square(10))
```

![](../images/generic/bool20.png) ![](../images/generic/bool21.png) </br>
![](../images/generic/bool22.png) ![](../images/generic/bool23.png)
