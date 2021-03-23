:ru
# Иерархические сборки.

При отображении сложной или анимированной сцены необъходимо работать с большим количеством связанных интерактивных объектов, перемещающихся друг относительно друга по определённым законам.

Для облегчения реализации такого поведения в zencad представлена библиотека zencad.assemble и её основное средство zencad.assemble.unit.
:en
# Hierarchical assemblies.

When displaying a complex or animated scene, it is necessary to work with a large number of connected interactive objects that move relative to each other according to certain laws.

To facilitate this behavior, zencad provides the zencad.assemble library and its main tool zencad.assemble.unit. 
::

------------------------------------------------------------
:ru
## Сборочный юнит (zencad.assemble.unit).
Сборочный юнит - это объект, имеющий собственную локальную систему координат, относительно которой позиционируются связанные с этим юнитом интерактивные объекты и другие юниты. Юниты могут создавать структуру дерева, отсчитывая своё положение относительно положения юнита-предка (unit.parent). Если юнит не имеет предка, его положение отсчитывается от глобальной системы координат.

Юнит содержит имеет два объекта координатного преобразования - location и global_location. 

- location - задаёт положение юнита относительно положения юнита предка. location может быть обновлён или непосредственно, или с помощью метода relocate.
- global_location - это положение юнита относительно глобальной системы координат. global_location используется при отрисовке объекта. global_location строится на основе дерева unit.location и может быть обновлён с помощью метода location_update, relocate и, с помощью других операций.
:en
## Assembly unit (zencad.assemble.unit).
An assembly unit is an object that has its own local coordinate system, relative to which interactive objects and other units associated with this unit are positioned. Units can create a tree structure by counting their position relative to the position of the parent unit (unit.parent). If the unit does not have an ancestor, its position is measured from the global coordinate system.

The unit contains two coordinate transformation objects - location and global_location.

- location - sets the position of the unit relative to the position of the ancestor unit. location can be updated either directly or using the relocate method.
- global_location is the position of the unit relative to the global coordinate system. global_location is used when rendering an object. global_location is built from the unit.location tree and can be updated using location_update, relocate and other operations. 
::

------------------
:ru
## Добавление объекта. 
Создаёт и связывает с юнитом интерактивный объект на основе переданного геометрического объекта _obj_.

Если в качестве параметра передан интерактивный объект, юнит берёт его под управление. (Примечание: юнит управляет расположением интерактивного объекта).

Сигнатура:
:en 
## Adding an object.
Creates and links to the unit an interactive object based on the passed geometry object _obj_.

If an interactive object is passed as a parameter, the unit takes control of it. (Note: the unit controls the location of the interactive object).
::

Signature: 
```python
u.add(obj, color=zencad.default_color)
```

Пример:
```
m = box(10)
i = interactive_object(box(10).right(20))
u.add(m)
u.add(i)
``` 

--------------------------------
:ru
## Добавление юнита-потомка.
Устанавливает объект _u_ предком для объекта _child_.
Теперь положение объектов в юните _child_ (и его потомках) будет расчитываться с учётом положения объекта _u_.
:en
## Adding a child unit.
Sets the _u_ object to be the ancestor of the _child_ object.
Now the position of objects in the unit _child_ (and its descendants) will be calculated taking into account the position of the object _u_. 
::


Сигнатура:
```python
u.link(child)
```

Пример:
```python
***
```

-------------------------------
:ru
## Обновить глобальное расположение.
Обновить глобальное расположение объекта согласно данным о его текущем положении и объекту глобального положения предка. 
view - если объект отображен, перерисовать его, исходя из нового положения.
deep - применить рекурсивно всех потомков объекта.
:en
## Update global position.
Update the global position of the object according to its current position and the global position of the ancestor object.
view - if the object is displayed, redraw it based on the new position.
deep - apply recursively all descendants of an object. 
::

Сигнатура:
```python
u.location_update(deep=True, view=True)
```

-----------------------------------------
:ru
## Изменить локальное положение.
Изменить текущее положение на объект location и применить процедуру location_update с опциями deep, view.
:en
## Update local position.
Change current position to location object and apply location_update procedure with deep, view options.
::

Сигнатура:
```python
u.relocate(location, deep=True, view=True)
```

----------------------
:ru
## Отобразить на сцене.
:en
## Display on stage. 
::

Сигнатура:
```python
u.bind_scene(scene, color=zencad.default_color, deep=True):
```
:ru
Добавить юнит в сцену scene. Все объекты, цвета которых не установлены, будут окрашены в default_color. Если deep, рекурсивно добавить в сцену все зависимые юниты.
:en
Add unit to scene scene. All objects whose colors are not set will be colored in default_color. If deep, recursively add all dependent units to the scene. 
::