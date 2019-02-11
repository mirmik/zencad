# Топологически зависимые преобразования

Существует класс операций, требующий в качестве параметра выбрать элемент топологии модели. В интерактивных CAD мы можем, используя указатель мыши, выделить такой элемент и указать в качестве параметра. Этот метод недоступен в скриптовом CAD. Общий подход ZenCad состоит в том, что такой элемент задаётся методом "ближайшей точки". При задании аргумента, вместо элемента топологии задаётся точка. Выбранным считается элемент, растояние до которого от элемента топологии будет минимальным. 

---
## Fillet
Операция скругления тела. 
Если тело объёмное - модификации подвергаются ребра. Если плоское - вершины.
Скругления задаются радиусом `r` и масивом ближайших точек `refs`. Если `refs == None`, выбранными считаются все элементы топологии. 

```python
fillet(shp=model, r=radius, refs=referencedPoints)
fillet(shp=model, r=radius)
model.fillet(radius, referencedPoints)
model.fillet(radius)
```
![](images/generic/fillet0.png)
![](images/generic/fillet1.png)
![](images/generic/fillet2.png)
![](images/generic/fillet3.png)
![](images/generic/fillet4.png)
![](images/generic/fillet5.png)

---
## Chamfer
Операция взятия фаски тела. В отличие от скругления применяется только к объёмным телам.
Фаска задаётся расстоянием `r`, взятым от ребра до линии фаски и масивом ближайших точек `refs`. Если `refs == None`, выбранными считаются все элементы топологии. 

TODO: несиметричная фаска. 

```python
chamfer(shp=model, r=radius, refs=referencedPoints)
```
![](images/generic/chamfer0.png)
![](images/generic/chamfer1.png)
![](images/generic/chamfer2.png)
![](images/generic/chamfer3.png)



---
## Thicksolid
Операция создания тонкостенного объёмного тела.
Задаётся прототипной моделью `shp` и массивом точек, ближайших к удаляемым граням `refs`.
Также задаётся толщина стенок `t`. Если толщина стенок положительная, стенки наращиваются наружу. Если отрицательная - внутрь.

```python
thicksolid(shp=model, t=thickness, refs=referencedPoints)
```

![](images/generic/thicksolid0.png)
![](images/generic/thicksolid1.png)