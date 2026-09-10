# Анимация, ввод и камера

В редакторе callback выполняется в изолированном runner. GUI владеет постоянным viewer и получает изменения представления. Аргумент callback — состояние ZenCad, не `DisplayWidget`.

Сохраните как `animation.py` и откройте командой `zencad animation.py`:

```python
import zencad as z

controller = z.display(z.box(10, center=True))

def animate(state):
    controller.relocate(z.rotateZ(state.loctime) * z.right(20))
    if state.input.key_pressed("Space"):
        controller.hide(not controller.is_hidden())
    state.camera.orbit((0, 0, 1), z.deg(15) * state.delta)

z.show(animate=animate, animate_step=0.02)
```

`loctime` — время с начала анимации в секундах, `delta` — интервал кадра. Доступны также `start_time`, `time`, `last_time`. `animate_step` задаёт желаемый шаг, а не гарантию точной частоты; движение по `delta` не зависит от фактической скорости кадров.

`state.input.key_down()` читает удерживаемую клавишу, `key_pressed()`/`key_released()` — переход в текущем кадре. Для упорядоченных событий есть `state.input.events`, для мыши — position/delta/buttons/wheel. Не заменяйте обработчики Qt вручную.

`state.camera.orbit(axis, angle)` задаёт относительный поворот камеры вокруг мировой оси, угол в радианах. Он применяется к текущей GUI-камере и сочетается с ручным вращением мышью. Камера может анимироваться без изменения модели.

## Ограничения managed-сцены

Создайте всю геометрию до `show()`. Callback может менять размещение, цвет и видимость, но не добавлять/удалять формы и не заменять их BREP. Деревья `assemble.unit` поддерживают изменение размещения существующих частей.

`preanimate`, произвольные QWidget-панели и прямой доступ к viewer не поддерживаются managed runner. `close_handle` доступен для анимированной managed-сессии, но не для статической. Standalone-путь имеет отдельный контракт; пример выше предназначен для редактора.

`inspect`, `check` и `render` ожидают конечную статическую сцену, поэтому отвергают анимированный `show()`. Подробности: [managed migration](../development/managed-animation-migration.md).
