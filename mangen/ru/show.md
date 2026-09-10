# Отображение

## Scene
Scene - это контейнер, хранящий модели и закреплённые за ними цвета.
```python
scene = Scene()
scene.add(model)
scene.add(model, color)
```
`scene.add` возвращает interactive_object, с помощью которого можно изменять состояние отображаемого объекта (см. [interactive_object](interactive_object.html))


---
## zencad.display
Инструмент для добавления геометрии в сцену.

```python
zencad.display(shape, color=None, scene=None)
zencad.display(unit, color=None, scene=None, deep=True)
zencad.display(lst, color=None, scene=None)

zencad.disp(model) # alternate
```
В зависимости от типа параметра, display может вести себя следующим образом:
Для shape - добавляет в сцену, возвращает interactive_object
Для assemble.unit - вызывает процедуру bind_to_scene, возвращает сам юнит
Для list - вызывает итеративно display для элементов списка, возвращает список результатов.

---
## zencad.highlight
Специальный вариант функции display, используемый для отладки конструируемой
геометрии.
```python
zencad.highlight(model, color=zencad.Color(0.5, 0, 0, 0.5))
zencad.hl(model) # alternate naming
```
В отличии от display функция возвращает переданный ей объект.
Пример использования (подсветим вычитаемую форму):
```python
c = a - hl(b.up(100500))
```

## Color
Объект, содержащий информацию о цвете в формате rgba. Диапазон значений параметров [0,1].
```python
Color(r,g,b,a)
```
ZenCad определяет стандартный набор цветов:
```python
zencad.color.white =     zencad.Color(1,1,1)
zencad.color.black =     zencad.Color(0,0,0)
zencad.color.red =       zencad.Color(1,0,0)
zencad.color.green =     zencad.Color(0,1,0)
zencad.color.blue =      zencad.Color(0,0,1)
zencad.color.yellow =    zencad.Color(1,1,0)
zencad.color.magenta =   zencad.Color(1,0,1)
zencad.color.cian =      zencad.Color(0,1,1)
zencad.color.mech =      zencad.Color(0.6, 0.6, 0.8)
zencad.color.transmech = zencad.Color(0.6, 0.6, 0.8, 0.8)
```

## show
```python
zencad.show(scene=None,
			animate=None, preanimate=None, close_handle=None)
```
Функция show инициирует отображение программы визуализатора. Если функция вызывается без аргументов, отображается сцена по умолчанию .

show также имеет набор параметров для поддержки фунций анимации модели (см. [Анимация](animate.html)).

Поведение функции show более подробно освещается в ([Внутренняя кухня](internal.html))


## Сцена в редакторе и имена объектов

GUI владеет одним постоянным viewer. Скрипт вычисляется в изолированном процессе
и передаёт сцену для отображения. При перезапуске скрипта вычислительный процесс
можно заменить, сохранив окно viewer. Изменения представления анимированных
объектов передаются отдельно от исходной геометрии.

```python
import zencad as z

part = z.box(10)
controller = z.display(part, name="housing", color=z.Color(0.2, 0.6, 0.8))
z.show()
```

`disp` — короткое имя `display`. Функция добавляет объект в сцену; возвращённый контроллер управляет его представлением. В managed runner это логический `SceneObjectRef`, а не объект Qt/AIS. Публичного `zencad.default_scene` нет: вызов без `scene=` использует внутреннюю сцену по умолчанию. Для явной локальной сцены доступны `z.Scene()` и `display(..., scene=scene)`.

Имена `name=` должны быть уникальными в сцене и задаются одному объекту, не списку. Автоматический ID и пользовательское имя — разные поля. Имена видны в inspect и manifest, ими удобно обозначать детали модели.

`Color(r, g, b, a=0)` принимает компоненты от 0 до 1. Четвёртая компонента — прозрачность: 0 непрозрачно, 1 прозрачно. Готовые цвета: `z.red`, `z.green`, `z.blue`, `z.yellow`, `z.white`, `z.mech`.

`highlight()`/`hl()` показывает форму и возвращает саму форму, поэтому может использоваться внутри булевого выражения. Контроллер отображения и геометрическая форма имеют разные назначения: [управление объектом](interactive_object.html).

## Именованный manifest без GUI

```python
import zencad as z

with z.managed_scene(1) as draft:
    z.display(z.box(2), name="housing")
    manifest = draft.manifest()
    print(manifest.to_json())
```

Manifest содержит идентичность и свойства отображения без BREP/mesh payload. Для площади, объёма и валидности используйте [inspect](headless.html). Для анимации — [managed callback](animate.html).
