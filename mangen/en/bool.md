# Boolean operations.

CSG geometry is operated on boolean operations. Zencad provides operations for joining, subtracting and intersecting 3d and 2d objects. There are two groups of these operations in zencad:

* over arrays of bodies using the functions _union_, _difference_, _intersect_
* over pairs of bodies using the operators _ + _ _-_ _ ^ _

>! Note:
>! Do not attempt to boolean a compound line from simple lines or sew a shell from faces. For these manipulations, there are special stitching procedures outlined in the relevant sections. 

---
## Union.

Сигнатура:
```python
# Функция:
result = union(array)

# Оператор:
result = shp0 + shp1
```

Пример:
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
![](../images/generic/union.png) ![](../images/generic/union0.png)   </br>
![](../images/generic/union1.png) ![](../images/generic/union2.png)  

---
## Difference.
Сигнатура:
```python
# Функция:
result = difference(array)

# Оператор:
result = shp0 - shp1
```

Пример:
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
![](../images/generic/difference.png) ![](../images/generic/difference0.png)   </br>
![](../images/generic/difference1.png) ![](../images/generic/difference2.png)  

---
## Intersect.

Сигнатура:
```python
# Функция:
result = intersect(array)

# Оператор:
result = shp0 ^ shp1
```

Пример:
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
![](../images/generic/intersect.png) ![](../images/generic/intersect0.png)   </br>
![](../images/generic/intersect1.png) ![](../images/generic/intersect2.png)  

---
## Crossing shells.
Let's twin the operation _intersect_, which calculates the intersection of the shells of bodies. 

Сигнатура:
```python
# Функция:
result = section(a, b)
```

Пример:
```python
m0 = section(box(10, center=True) - sphere(4))
m1 = section(box(10, center=True), sphere(7))

```
![](../images/generic/section0.png)
![](../images/generic/section1.png)   

---
## Splitting and slicing by a plane.

`split(body, tools)` partitions a body with Shape tools; `slice(body, z=..., axis=...)` uses one plane. Both return collections of solids and retain uncut bodies. An empty set of tools for `split` raises `ValueError`.

The parts returned by `slice` are ordered along the plane normal. With two parts, unpack the result as `lower, upper`. See [Splitting bodies](split.html) for details and examples.

```python
parts = split(box(10), (infplane().up(3), infplane().up(7)))

lower, upper = slice(box(10), z=4)
left, right = slice(box(10), z=2, axis="x")
negative, positive = slice(box(10), plane=((0, 5, 0), (0, 1, 0)))
```

---------------------------------------------
## Boolean operations on 2D solids.
Just like with 3D objects, the above operations can be applied to 2D objects as long as they are in the same plane. 

Пример:
```python
m0 = circle(10) - square(10)
m1 = circle(10) + square(10)
m2 = circle(10) ^ square(10)
m3 = section(circle(10), square(10))
```

![](../images/generic/bool20.png) ![](../images/generic/bool21.png) </br>
![](../images/generic/bool22.png) ![](../images/generic/bool23.png)
