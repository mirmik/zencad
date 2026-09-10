# Отображение

## display и disp

`display` добавляет геометрию в сцену. `disp` — её короткое имя. Возвращённый контроллер позволяет менять [размещение, цвет и видимость](interactive_object.html) объекта.

```python
from zencad import *

controller = display(box(10), color=Color(0.2, 0.6, 0.8), name="housing")
show()
```

Для списка `display` возвращает список контроллеров, для сборочного `unit` — сам юнит. Имена `name=` задаются отдельным объектам и должны быть уникальными в сцене. Они видны в отчётах [inspect](headless.html).

## Color

`Color(r, g, b, a=0)` принимает компоненты от 0 до 1. Первые три задают RGB, четвёртая — прозрачность: 0 непрозрачно, 1 полностью прозрачно.

```python
from zencad import *

display(box(10), color=Color(0.2, 0.6, 0.8, 0.5))
display(sphere(3).right(15), color=yellow)
show()
```

Готовые цвета доступны по именам `white`, `black`, `red`, `green`, `blue`, `yellow`, `magenta`, `cian`, `mech`, `transmech`, а также через модуль `zencad.color`.

## highlight и hl

Подсветка добавляет форму в сцену и возвращает саму форму. Это удобно для показа вычитаемого объёма прямо в выражении:

```python
from zencad import *

body = box(20) - hl(cylinder(4, 20).translate(10, 10, 0))
display(body)
show()
```

## show и явная сцена

`show()` отображает собранную сцену. При запуске скрипта из редактора результат появляется в его окне; при прямом запуске `python model.py` открывается отдельный просмотрщик.

Обычно используется сцена по умолчанию. При необходимости можно создать свою:

```python
from zencad import *

scene = Scene()
scene.add(box(10), color=blue)
display(sphere(3).right(15), color=yellow, scene=scene)
show(scene)
```

`scene.add()` также возвращает контроллер объекта. Параметры `animate` и `animate_step` функции `show` описаны в разделе [«Анимация»](animate.html), устройство отображения — во [«Внутренней кухне»](internal.html).
