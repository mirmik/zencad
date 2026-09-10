# Интерактивный объект

Интерактивный объект - есть единица отображения в zencad.

В этом разделе перечислены типы интерактивных объектов и указаны методы соответствующего базового класса.

----------------------------------------------
## Геометрические интерактивные объекты.
Механизм интерактивных объектов используется для отображения геометрических форм, обрабатываемых zencad.

Пример 1 (Создание интерактивного объекта формы):
```python3
model = zencad.box(10)
scn = zencad.Scene()

intobj = zencad.display(model, scene=scn)

zencad.show(scn)
```

Пример 2 (Создание интерактивного объекта формы с помощью функции отображения disp):
```python3
model = zencad.box(10)

intobj = zencad.disp(model)
intobj.set_color(zencad.color.yellow)
```

---------------------------------------
## Методы класса interactive_object:

### Переразмещение  
```python3
intobj.relocate(trans)
```
Переразмещает объект в положение _trans_ относительно исходного расположения.

### Скрытие
```python3
intobj.hide(True)
```
Скрыть или же вновь отобразить объект. Скрытый объект не удаляется из памяти.

### Установка цвета
```python3
intobj.set_color(color)

# Examples:
# RGB:
intobj.set_color((0.2,0.3,0.6))
intobj.set_color(zencad.Color(0.2,0.3,0.6))

# RGBA:
intobj.set_color((0.2,0.3,0.6,0.5))
intobj.set_color(zencad.Color(0.2,0.3,0.6,0.5))
```
Изменить цвет интерактивного объекта.
Параметр color представляет или кортеж или объект zencad.Color.

## Управление объектом в редакторе

Геометрическая операция создаёт новую форму. Контроллер, возвращённый `display()`, меняет представление уже добавленного объекта:

```python
import zencad as z

with z.managed_scene(1):
    body = z.box(10)
    controller = z.display(body, name="part")
    controller.relocate(z.right(20))
    controller.set_color(z.yellow)
    controller.hide(True)
    assert controller.is_hidden()
    controller.hide(False)
```

`relocate(transform)` задаёт размещение, `location()` читает его; `set_color()`/`color()` меняют и читают цвет, `hide()`/`is_hidden()` — видимость. Контроллер также поддерживает helpers преобразований. Для каждого кадра обычно задавайте абсолютное размещение через `relocate`, чтобы не накапливать преобразования случайно.

Это не изменение BREP и не булева операция: исходный `body` остаётся прежним. В managed-анимации обновляются только свойства заранее созданных объектов. Не создавайте `interactive_object` или QWidget вручную ради изменения модели. [Анимация](animate.html).

## Графические интерактивные объекты.
Помимо интерактивных объектов геометрических форм существуют интерактивные объекты, которые могут использоваться для передачи дополненительной информации на рабочей сцене:

---
### Стрелка:

Отобразить стрелку, соответствующую вектору _vec_, ведущему из точки _pnt_, размер головы стрелки определяется параметром _arrlen_, толщина линии параметром _width_.
Объект добавляется в сцену вызовом `display()`.

```python3
from zencad.interactive.line import arrow

display(arrow(pnt, pnt + vec, color=zencad.white, arrlen=5, width=1))
```

---
### Линия:
Отобразить линию, между точками _apnt_ и _bpnt_, толщина линии параметром _width_.
Объект добавляется в сцену вызовом `display()`.

```python3
from zencad.interactive.line import line as display_line

display(display_line(apnt, bpnt, color=zencad.white, width=1))
```

----------------------------------

Эти функции принимают начальную и конечную точки и создают объекты отображения; `zencad.line` создаёт геометрическую кривую и имеет другое назначение.

```python
import zencad as z
from zencad.interactive.line import arrow, line as display_line

with z.managed_scene(1):
    z.display(arrow((0, 0, 0), (10, 0, 0), color=z.red, arrlen=2))
    z.display(display_line((0, 0, 0), (0, 10, 0), color=z.green))
```
