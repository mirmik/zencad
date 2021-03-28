:ru
# Рефлексия
Сложные геометрические объекты состоят из более простых. Данная группа функций и методов позволяет расскладывать сложные объекты на образующие их компоненты.

Для работы с эими фунциями рекомендуется изучить топологическое устройство brep моделей в ядре _OpenCascade_. (Начать ознаклмление можно с раздела [Введение в BREP представление геометрических моделей](geomcore.html))
:en
# Reflection
Complex geometric objects are composed of simpler ones. This group of functions and methods allows you to decompose complex objects into their constituent components.

To work with these functions, it is recommended to study the topological structure of models in the _OpenCascade_ kernel. (You can get started with the section [Introduction to BREP Representation of Geometric Models](geomcore.html)) 
::

---------------------------
:ru
## Пустой объект
Возвращает истину, если объект пустой, иначе ложь.
:en
## Empty object
Returns true if the object is empty, false otherwise.
::

Сигнатура:
```python
shp.is_nullshape()
```
Пример:
```python
a = box(10, center=True)
b = sphere(r=10)
(a - b).is_nullshape() # True
```

---------------------------
:ru
## Массивы базовых объектов
Это семейство методов позволяет извлечь и отфильтровать необходимые базовые объекты. 

Все методы имеют однотипную сигнатуру, возвращают массив объектов соответствующего типа. Необязательная опция _filter_ позволяет отфильтровать выборку по необходимому условию.
:en
## Arrays of base objects
This family of methods allows you to retrieve and filter the underlying objects you need.

All methods have the same signature and return an array of objects of the corresponding type. The optional _filter_ option allows you to filter the selection by a necessary condition. 
::
```python
shape.vertices(filter=None) # -> [point3]
shape.solids(filter=None) # -> [Shape; future:Solid] 
shape.faces(filter=None) # -> [Face]
shape.edges(filter=None) # -> [Edge]
shape.wires(filter=None) # -> [Shape; future:Wire]
shape.shells(filter=None) # -> [Shape; future:Shell]
shape.compounds(filter=None) # -> [Shape; future:Compound]
shape.compsolids(filter=None) # -> [Shape; future:Compsolid]
```

---------------------------------------------------
:ru
## Взятие базового объекта по методу ближайшей точки
Иногда требуется извлечь из сложного объекта конкретный базовый объект. 
В этом случае можно использовать метод базовой точки.  

Следующие функции реализуют метод ближайшей точке и возвращают ближайший к _pnt_ базовый объект соответствующего типа, принадлежащий сложному объекту _shp_.
:en
## Taking a base object using the closest point method
Sometimes you want to extract a specific base object from a complex object.
In this case, you can use the base point method.

The following functions implement the closest point method and return the closest base object of the corresponding type to _pnt_ belonging to the complex _shp_ object. 
::

```python
near_edge(shp, pnt) # -> Edge
near_face(shp, pnt) # -> Face
near_vertex(shp, pnt) # -> point3
```

---
:ru
## Восстановление типа
zencad выводит тип объекта и применимые к нему операции на основе дерева построения, что в некоторых случаях может давать неверный результат.

Функция restore_shapetype восстанавливает тип на основе анализа реального представления объекта. 
:en
## Type restoration
zencad displays the type of object and the operations applicable to it based on the build tree, which in some cases may give incorrect results.

The restore_shapetype function restores the type based on the analysis of the object's real representation. 
::

```python
original_shp = restore_shapetype(shp)
```