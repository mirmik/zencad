:ru
# Анимация
Графический интерфейс позволяет анимировать отображаемую сцену.

> Примечание о миграции: managed runtime поддерживает базовый
> `show(animate=...)`. Callback исполняется в отдельном вычислительном процессе,
> а изменения `relocate`, `set_color` и `hide` применяются к постоянному viewer
> через `ScenePatch`. Типизированный ввод с клавиатуры и мыши доступен через
> `state.input`. Относительное вращение камеры доступно через Qt-free фасад
> `state.camera`: `state.camera.orbit(axis, angle)` принимает мировую ось и
> угол в радианах. GUI применяет команду к текущей камере, поэтому ручная
> навигация остаётся базой для последующей анимации.
> Произвольные PyQt-виджеты, `preanimate` и прямой доступ к viewer не входят в
> новый контракт.

Пример:
:en
# Animation
The graphical interface allows you to animate the displayed scene.

> Migration note: the managed runtime supports basic `show(animate=...)`.
> Callbacks execute in the isolated runner, while `relocate`, `set_color`, and
> `hide` mutations reach the persistent viewer as `ScenePatch` values. Typed
> keyboard/mouse input is available through `state.input`. Relative camera
> orbit is available as `state.camera.orbit(axis, angle)`; the GUI applies it
> to the current camera, so manual navigation remains authoritative. Arbitrary
> PyQt widgets, `preanimate`, and
> direct viewer access are outside the new contract.

Example: 
::

```python3
s = box(10, center=True)
controller = disp(s)
nulltime = time.time()

def animate(widget):
	trans = rotateZ(time.time() - nulltime) * right(30)
	controller.relocate(trans)

show(animate=animate) 
```

:ru
Здесь мы используем специальную функцию анимации `animate`, которая, используя объект контроллер, возвращенный функцией disp, в зависимости от текущего момента времени обновляет местоположение контролируемого объекта.
В качестве параметра метода `relocate` выступает объект преобразования. (Подробнее в [Преобразования](trans0.html), [Комбинации преобразований](trans1.html))

Кроме параметра `animate` функция show имеет связанные параметры `preanimate` и `close_handle`. `preanimate` принимает функцию, вызывающуюся один раз до первой итерации `animate`, но уже после создания графического окружения. `close_handle` вызывается как обработчик при завершении процесса.
:en
Here we use a special animation function `animate`, which, using the controller object returned by the disp function, updates the location of the controlled object based on the current moment in time.
The transformation object is used as a parameter of the `relocate` method. (More details in [Transformations](trans0.html), [Transformations](trans1.html))

In addition to the `animate` parameter, the show function has associated` preanimate` and `close_handle` parameters. `preanimate` takes a function that is called once before the first iteration of` animate`, but after the graphical environment has been created. `close_handle` is called as a handler when the process ends. 
::
