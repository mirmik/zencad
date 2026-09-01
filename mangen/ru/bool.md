:ru
# Булевы операции.

CSG геометрия операется на булевы операции. В zencad представлены операции объединения, вычитания и пересечения 3д и 2д объектов. В zencad есть два группы этих операций: 

* над массивами тел с помощью функций _union_, _difference_, _intersect_
* над парами тел с помощью операторов _+_ _-_ _^_

>! Примечание:
>! Не стоит пытаться с помощью булевых операций получить составную линию из простых линий или сшить оболочку из граней. Для этих манипуляций, существуют специальные процедуры сшивки, освещенные в соответствующих разделах.
:en
# Boolean operations.

CSG geometry is operated on boolean operations. Zencad provides operations for joining, subtracting and intersecting 3d and 2d objects. There are two groups of these operations in zencad:

* over arrays of bodies using the functions _union_, _difference_, _intersect_
* over pairs of bodies using the operators _ + _ _-_ _ ^ _

>! Note:
>! Do not attempt to boolean a compound line from simple lines or sew a shell from faces. For these manipulations, there are special stitching procedures outlined in the relevant sections. 
::

---
:ru
## Объединение тел.
:en
## Union.
::

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
:ru
## Вычитание тел.
:en
## Difference.
::
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
:ru
## Пересечение тел.
:en
## Intersect.
::

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
:ru
## Пересечение оболочек.
Побратим операции _intersect_, производящий вычисление пересечения оболочек тел.  
:en
## Crossing shells.
Let's twin the operation _intersect_, which calculates the intersection of the shells of bodies. 
::

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
:ru
## Разбиение и сечение плоскостью.

`split(body, tools)` делит тело одним или несколькими Shape-инструментами и
возвращает `SplitResult` — ленивую детерминированно упорядоченную
последовательность получившихся solid-частей. Пустой набор инструментов и
инструмент, который не делит тело (включая касание), приводят к `ValueError`.

`slice(body, z=..., axis=...)` — удобный частный случай для плоскости. Результат
`SliceResult` можно распаковать как `(lower, upper)`; порядок идёт от
отрицательной к положительной стороне нормали. Произвольная плоскость задаётся
плоской гранью или парой `(origin, normal)`. Если получилось не ровно два
solid-тела, операция неоднозначна и поднимает `ValueError`.
:en
## Splitting and slicing by a plane.

`split(body, tools)` partitions a body with one or more Shape tools and returns
a `SplitResult`: a lazy, deterministically ordered sequence of resulting
solids. Empty tools and a tool that does not divide the body (including a
tangent tool) raise `ValueError`.

`slice(body, z=..., axis=...)` is the convenient plane form. Its `SliceResult`
unpacks as `(lower, upper)`, ordered from the negative to the positive side of
the plane normal. An arbitrary plane may be a planar face or an
`(origin, normal)` pair. A result other than exactly two solids is ambiguous
and raises `ValueError`.
::

```python
parts = split(box(10), (infplane().up(3), infplane().up(7)))

lower, upper = slice(box(10), z=4)
left, right = slice(box(10), z=2, axis="x")
negative, positive = slice(box(10), plane=((0, 5, 0), (0, 1, 0)))
```

---------------------------------------------
:ru
## Булевы операции над двумерными телами.
Точно также как и к трёхмерным объектам, перечисленные выше операции могут применяться к двумерным объектам до тех пор, пока они находятся в одной плоскости.
:en
## Boolean operations on 2D solids.
Just like with 3D objects, the above operations can be applied to 2D objects as long as they are in the same plane. 
::

Пример:
```python
m0 = sphere(10) - square(10)
m1 = sphere(10) + square(10)
m2 = sphere(10) ^ square(10)
m2 = section(sphere(10), square(10))
```

![](../images/generic/bool20.png) ![](../images/generic/bool21.png) </br>
![](../images/generic/bool22.png) ![](../images/generic/bool23.png)
