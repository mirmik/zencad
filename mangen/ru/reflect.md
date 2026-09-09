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
## Проверка состава
Для результата объёмной операции отсутствие тел можно проверить через `len(shape.solids()) == 0`. Это проверка наличия solid-компонентов, а не универсальная проверка пустоты: непустая грань или линия тоже не содержит solid.
:en
## Checking contents
For a solid operation, test `len(shape.solids()) == 0` to check that no solid components remain. This is not a general emptiness test: a nonempty face or curve contains no solids either.
::

Сигнатура:
```python
len(shp.solids()) == 0
```
Пример:
```python
a = box(10, center=True)
b = sphere(r=10)
len((a - b).solids()) == 0 # True
```

---------------------------
:ru
## Массивы базовых объектов
Это семейство методов позволяет извлечь и отфильтровать необходимые базовые объекты. 

Методы возвращают `ShapeList` с элементами соответствующего типа. Для отбора используйте методы коллекции: `filter_by`, `filter_by_position`, `planar` и другие [селекторы](selectors.html). Вершина — объект `Vertex`; её координаты доступны через `.point()`.
:en
## Arrays of base objects
This family of methods allows you to retrieve and filter the underlying objects you need.

Methods return a `ShapeList` with the corresponding element type. Use collection methods such as `filter_by`, `filter_by_position` and `planar` for [selection](selectors.html). A vertex is a `Vertex`; obtain its coordinates with `.point()`.
::
```python
shape.vertices() # -> ShapeList[Vertex]
shape.solids() # -> ShapeList[Solid]
shape.faces() # -> ShapeList[Face]
shape.edges() # -> ShapeList[Edge]
shape.wires() # -> ShapeList[Wire]
shape.shells() # -> ShapeList[Shell]
shape.compounds() # -> ShapeList[Compound]
shape.compsolids() # -> ShapeList[CompSolid]
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
near_vertex(shp, pnt) # -> Vertex; .point() -> Point3
```

---
:ru
## Восстановление типа
Типы `Solid`, `Face`, `Edge` и другие доступны непосредственно. `restore_shapetype` анализирует состав формы и извлекает единственный подходящий компонент. Если нужен ровно один solid, выразите это явно: `shp.solids().only()`.
:en
## Type restoration
Types such as `Solid`, `Face` and `Edge` are directly available. `restore_shapetype` examines a shape and extracts a single suitable component. To require exactly one solid, use `shp.solids().only()`.
::

```python
original_shp = restore_shapetype(shp)
```
