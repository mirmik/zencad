:ru
# Отображение
:en
# Display 
::

## Scene
:ru
Scene - это контейнер, хранящий модели и закреплённые за ними цвета. 
:en
Scene is a container that stores models and their associated colors. 
::
```python
scene = Scene()
scene.add(model)
scene.add(model, color)
```
:ru 
`scene.add` возвращает interactive_object, с помощью которого можно изменять состояние отображаемого объекта (см. [interactive_object](interactive_object.html))

zencad.default_scene - объект сцены, используемый операциями связанными с отбражением, если не указано иное. 
:en
`scene.add` returns an interactive_object with which you can change the state of the displayed object (see [interactive_object](interactive_object.html))

zencad.default_scene - scene object used by display-related operations, unless otherwise specified.
::

---
## zencad.display
:ru
Инструмент для добавления геометрии в сцену.
:en
A tool for adding geometry to a scene.
::

```python
zencad.display(shape, color=zencad.default_color, scene=zencad.default_scene)
zencad.display(unit, color=zencad.default_color, scene=zencad.default_scene, deep=True)
zencad.display(lst, color=zencad.default_color, scene=zencad.default_scene)

zencad.disp(model) # alternate
```
:ru
В зависимости от типа параметра, display может вести себя следующим образом:
Для shape - добавляет в сцену, возвращает interactive_object
Для assemble.unit - вызывает процедуру bind_to_scene, возвращает None
Для list/tuple - вызывает итеративно display для элементов списка, возвращает список результатов.
:en
Depending on the type of the parameter, display can behave as follows:
For shape - adds to the scene, returns interactive_object
For assemble.unit - calls the bind_to_scene procedure, returns None
For list / tuple, it calls display iteratively on the list items, returns a list of results.
::

---
## zencad.highlight
:ru
Специальный вариант функции display, используемый для отладки конструируемой
геометрии.
:en
A special variant of the display function used to debug the constructed
geometry.
::
```python
zencad.highlight(model, color=zencad.color(0.5, 0, 0, 0.5))
zencad.hl(model) # alternate naming
```
:ru
В отличии от display функция возвращает переданный ей объект.
Пример использования (подсветим вычитаемую форму):
:en
Unlike display, the function returns the object passed to it.
Usage example (highlight the subtracted form):
::
```python
c = a - hl(b.up(100500))
```

## color
:ru
Объект, содержащий информацию о цвете в формате rgba. Диапазон значений параметров [0,1].
:en
An object containing color information in rgba format. The range of parameter values is [0,1].
::
```python
color(r,g,b,a)
```
:ru
ZenCad определяет стандартный набор цветов:
:en
ZenCad defines a standard set of colors:
::
```python
zencad.color.white =     zencad.color(1,1,1)
zencad.color.black =     zencad.color(0,0,0)
zencad.color.red =       zencad.color(1,0,0)
zencad.color.green =     zencad.color(0,1,0)
zencad.color.blue =      zencad.color(0,0,1)
zencad.color.yellow =    zencad.color(1,1,0)
zencad.color.magenta =   zencad.color(0,1,1)
zencad.color.cian =      zencad.color(1,0,1)
zencad.color.mech =      zencad.color(0.6, 0.6, 0.8)
zencad.color.transmech = zencad.color(0.6, 0.6, 0.8, 0.8)
```

## show
```python
zencad.show(scene=zencad.default_scene, 
			animate=None, preanimate=None, close_handle=None)
```
:ru
Функция show инициирует отображение программы визуализатора. Если функция вызывается без аргументов, отображается сцена по умолчанию (zencad.default_scene).

show также имеет набор параметров для поддержки фунций анимации модели (см. [Анимация](animate.html)).

Поведение функции show более подробно освещается в ([Внутренняя кухня](internal.html))
:en
The show function initiates the display of the renderer program. If the function is called with no arguments, the default scene (zencad.default_scene) is displayed.

show also has a set of parameters to support animation functions for the model (see [Animation](animate.html)).

The show behavior is covered in more detail in ([Internal Kitchen](internal.html)) 
::