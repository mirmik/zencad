# Анимация
Графический интерфейс позволяет анимировать отображаемую сцену.

> Migration note: the managed runtime supports basic `show(animate=...)`.
> Callbacks execute in the isolated runner, while `relocate`, `set_color`, and
> `hide` mutations reach the persistent viewer as `ScenePatch` values. Typed
> keyboard/mouse input is not implemented yet; arbitrary PyQt widgets,
> `preanimate`, and direct viewer access are outside the new contract.

Пример:

```python3
s = box(10, center=True)
controller = disp(s)
nulltime = time.time()

def animate(widget):
	trans = rotateZ(time.time() - nulltime) * right(30)
	controller.relocate(trans)

show(animate=animate) 
```

Здесь мы используем специальную функцию анимации `animate`, которая, используя объект контроллер, возвращенный функцией disp, в зависимости от текущего момента времени обновляет местоположение контролируемого объекта.
В качестве параметра метода `relocate` выступает объект преобразования. (Подробнее в [Преобразования](trans0.html), [Комбинации преобразований](trans1.html))

Кроме параметра `animate` функция show имеет связанные параметры `preanimate` и `close_handle`. `preanimate` принимает функцию, вызывающуюся один раз до первой итерации `animate`, но уже после создания графического окружения. `close_handle` вызывается как обработчик при завершении процесса.
