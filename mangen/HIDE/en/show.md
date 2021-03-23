# Отображение

## Scene
Scene - это контейнер, хранящий модели и закреплённые за ними цвета. 
```python
scene = Scene()
scene.add(model)
scene.add(model, color)
``` 
`scene.add` возвращает interactive_object, с помощью которого можно изменять состояние отображаемого объекта (см. [interactive_object](interactive_object.html))

zencad.default_scene - объект сцены, используемый операциями связанными с отбражением, если не указано иное. 

## zencad.display
Инструмент для добавления геометрии в сцену.

```python
zencad.display(shape, color=zencad.default_color, scene=zencad.default_scene)
zencad.display(unit, color=zencad.default_color, scene=zencad.default_scene, deep=True)
zencad.display(lst, color=zencad.default_color, scene=zencad.default_scene)

zencad.disp(model) # alternate
```

В зависимости от типа параметра, display может вести себя следующим образом:
Для shape - добавляет в сцену, возвращает interactive_object
Для assemble.unit - вызывает процедуру bind_to_scene, возвращает None
Для list/tuple - вызывает итеративно display для элементов списка, возвращает список результатов.

## zencad.highlight
Специальный вариант функции display, используемый для отладки конструируемой
геометрии.
```python
zencad.highlight(model, color=zencad.color(0.5, 0, 0, 0.5))
zencad.hl(model) # alternate naming
```
В отличии от display функция возвращает переданный ей объект.
Пример использования (подсветим вычитаемую форму):
```python
c = a - hl(b.up(100500))
```

## color
Объект, содержащий информацию о цвете в формате rgba. Диапазон значений параметров [0,1].
```python
color(r,g,b,a)
```
ZenCad определяет стандартный набор цветов:
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
Функция show инициирует отображение программы визуализатора. Если функция вызывается без аргументов, отображается сцена по умолчанию (zencad.default_scene).

show также имеет набор параметров для поддержки фунций анимации модели (см. [Анимация](animate.html)).

Поведение функции show более подробно освещается в ([Внутренняя кухня](internal.html))