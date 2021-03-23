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
![](../images/generic/union.png)
![](../images/generic/union0.png)  
![](../images/generic/union1.png)
![](../images/generic/union2.png)  

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
![](../images/generic/difference.png)
![](../images/generic/difference0.png)  
![](../images/generic/difference1.png)
![](../images/generic/difference2.png)  

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
![](../images/generic/intersect.png)
![](../images/generic/intersect0.png)  
![](../images/generic/intersect1.png)
![](../images/generic/intersect2.png)  

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
```
![](../images/generic/section0.png)
![](../images/generic/section1.png)   

---------------------------------------------
## Булевы операции над двумерными телами.
Точно также как и к трёхмерным объектам, перечисленные выше операции могут применяться к двумерным объектам до тех пор, пока они находятся в одной плоскости.

Пример:
```python
m0 = sphere(10) - square(10)
m1 = sphere(10) + square(10)
m2 = sphere(10) ^ square(10)
m2 = section(sphere(10), square(10))
```

![](../images/generic/bool20.png)
![](../images/generic/bool21.png)  
![](../images/generic/bool22.png)
![](../images/generic/bool23.png)
