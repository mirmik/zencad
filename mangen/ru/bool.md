# Булевы операции и сечения.

CSG геометрия операется на булевы операции. В zencad представлены операции объединения, вычитания и пересечения 3д объектов. В zencad есть два способа выполнения этих операций: 

* над массивами тел с помощью функций `union`, `difference`, `intersect`
* над парами тел с помощью операторов `+` `-` `^`

---
## Объединение тел.
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

------------------------------
## Сечения.
Поиск рёбер пересечения пары тел.

Операция _section_ похожа на _intersect_, только результатом является не твердое тело, а рёбра пересечений. 

```python
section(a, b=0)
```

Аргументы _a_ и _b_ - пересекаемые тела. Если один из аргументов действительное число или вектор, то на основе этого параметра строится тело в виде плоскости пересечения.

### Пример. Пересечение оболочек разности куба и сферы горизонтальной плоскостью.
```python
body = box(10, center=True) - sphere(4)
sect = section(body)
```
![](../images/generic/section0.png)  

### Пример. Пересечение оболочек куба и сферы.
```python
a = box(10, center=True) 
b = sphere(7)
sect = section(a, b)
```
![](../images/generic/section1.png)