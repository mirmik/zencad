# Булевы операции.

CSG геометрия операется на булевы операции. В zencad представлены операции объединения, вычитания и пересечения 3д и 2д объектов. В zencad есть два группы этих операций: 

* над массивами тел с помощью функций _union_, _difference_, _intersect_
* над парами тел с помощью операторов _+_ _-_ _^_

>! Примечание:
>! Не стоит пытаться с помощью булевых операций получить составную линию из простых линий или сшить оболочку из граней. Для этих манипуляций, существуют специальные процедуры сшивки, освещенные в соответствующих разделах.

---
## Объединение тел.

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
## Вычитание тел.
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
## Пересечение тел.

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
## Пересечение оболочек.
Побратим операции _intersect_, производящий вычисление пересечения оболочек тел.  

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

```python
parts = split(box(10), (infplane().up(3), infplane().up(7)))

lower, upper = slice(box(10), z=4)
left, right = slice(box(10), z=2, axis="x")
negative, positive = slice(box(10), plane=((0, 5, 0), (0, 1, 0)))
```

---------------------------------------------
## Булевы операции над двумерными телами.
Точно также как и к трёхмерным объектам, перечисленные выше операции могут применяться к двумерным объектам до тех пор, пока они находятся в одной плоскости.

Пример:
```python
m0 = circle(10) - square(10)
m1 = circle(10) + square(10)
m2 = circle(10) ^ square(10)
m3 = section(circle(10), square(10))
```

![](../images/generic/bool20.png) ![](../images/generic/bool21.png) </br>
![](../images/generic/bool22.png) ![](../images/generic/bool23.png)
