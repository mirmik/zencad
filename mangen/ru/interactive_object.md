:ru
# Управление отображаемым объектом

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
:en
# Controlling displayed objects

A geometry operation creates a new shape. The controller returned by `display()` changes the presentation of an existing scene object:

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

`relocate(transform)` sets placement and `location()` reads it; `set_color()`/`color()` update and read color; `hide()`/`is_hidden()` control visibility. Controllers also support transform helpers. Usually set an absolute placement each frame with `relocate` to avoid unintentionally accumulating transforms.

This does not change BREP or perform a boolean operation: the source `body` remains unchanged. Managed animation updates properties of objects created beforehand. Do not construct `interactive_object` or QWidget instances manually to update a model. [Animation](animate.html).
::
