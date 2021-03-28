:ru
# Интерактивный объект

Интерактивный объект - есть единица отображения в zencad.

В этом разделе перечислены типы интерактивных объектов и указаны методы соответствующего базового класса.
:en
# Interactive object

An interactive object is a display unit in zencad.

This section lists the types of interactive objects and specifies the methods of the corresponding base class. 
::

----------------------------------------------
:ru
## Геометрические интерактивные объекты.
Механизм интерактивных объектов используется для отображения геометрических форм, обрабатываемых zencad.

Пример 1 (Создание интерактивного объекта формы):
:en
## Geometric interactive objects.
The interactive object engine is used to display geometric shapes processed by zencad.

Example 1 (Creating an interactive form object): 
::
```python3
model = zencad.box(10)
scn = zencad.scene()

intobj = zencad.interactive_object(model) 
scn.add(intobj)

zencad.show(scn)
```

:ru
Пример 2 (Создание интерактивного объекта формы с помощью функции отображения disp):
:en
Example 2 (Create an interactive form object using the disp display function): 
::
```python3
model = zencad.box(10)

intobj = zencad.disp(model)
intobj.set_color(zencad.color.yellow)
```

---------------------------------------
:ru
## Графические интерактивные объекты.
Помимо интерактивных объектов геометрических форм существуют интерактивные объекты, которые могут использоваться для передачи дополненительной информации на рабочей сцене:
:en
## Graphical interactive objects.
In addition to interactive objects of geometric shapes, there are interactive objects that can be used to transfer additional information on the working stage: 
::

---
:ru
### Стрелка:

Отобразить стрелку, соответствующую вектору _vec_, ведущему из точки _pnt_, размер головы стрелки определяется параметром _arrlen_, толщина линии параметром _width_.
Если параметр scene не None, объект сразу добавляется в scene.
:en
### Arrow:

Show an arrow corresponding to the vector _vec_, leading from the point _pnt_, the size of the arrow head is determined by the _arrlen_ parameter, the line width by the _width_ parameter.
If scene is not None, the object is immediately added to scene. 
::

```python3
arrow(pnt, vec, clr=zencad.color.white, arrlen=5, width=1, scene=zencad.default_scene)
```

---
:ru
### Линия:
Отобразить линию, между точками _apnt_ и _bpnt_, толщина линии параметром _width_.
Если параметр scene не None, объект сразу добавляется в scene.
:en
### Line:
Show the line, between the points _apnt_ and _bpnt_, line width with the _width_ parameter.
If scene is not None, the object is immediately added to scene. 
::

```python3
line(apnt, bpnt, clr=zencad.color.white, width=1, scene=zencad.default_scene)
```

----------------------------------
:ru
## Методы класса interactive_object:

### Переразмещение  
:en
## Methods of the interactive_object class:

### Repositioning 
::
```python3
relocate(trans)
```
:ru
Переразмещает объект в положение _trans_ относительно исходного расположения. 

### Скрытие
:en
Relocates the object to the _trans_ position relative to its original location.

### Hiding 
::
```python3
hide(en=True/False)
```
:ru
Скрыть или же вновь отобразить объект. Скрытый объект не удаляется из памяти.

### Установка цвета
:en
Hide or re-display the object. The hidden object is not removed from memory.

### Color setting 
::
```python3
set_color(color)

# Examples:
# RGB:
intobj.set_color((0.2,0.3,0.6))
intobj.set_color(zencad.color(0.2,0.3,0.6))

# RGBA:
intobj.set_color((0.2,0.3,0.6,0.5))
intobj.set_color(zencad.color(0.2,0.3,0.6,0.5))
```
:ru
Изменить цвет интерактивного объекта. 
Параметр color представляет или кортеж или объект zencad.color.
:en
Change the color of the interactive object.
The color parameter represents either a tuple or a zencad.color object. 
::