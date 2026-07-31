:ru
# Анимация
Графический интерфейс позволяет анимировать отображаемую сцену.

> Примечание о миграции: постоянный viewer уже используется для статических
> сцен, но managed runtime пока не реализует `show(animate=...)`. Принята
> архитектура, в которой callback останется в вычислительном процессе,
> изменения `relocate`, `set_color` и `hide` будут передаваться как
> `ScenePatch`, а клавиатура и мышь — как типизированные `InputEvent` в обратную
> сторону. Произвольные PyQt-виджеты и прямой доступ к viewer поддерживаться не
> будут. До реализации этого контракта пример ниже описывает legacy runtime.

Пример:
:en
# Animation
The graphical interface allows you to animate the displayed scene.

> Migration note: the persistent viewer is already the default for static
> scenes, but the managed runtime does not yet implement `show(animate=...)`.
> The accepted design keeps callbacks in the runner, transports logical object
> mutations as `ScenePatch`, and returns typed keyboard/mouse `InputEvent`
> values. Arbitrary PyQt widgets and direct viewer access will not be supported.
> Until that contract is implemented, the example below describes the legacy
> runtime.

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
