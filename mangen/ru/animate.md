# Анимация
Графический интерфейс позволяет анимировать отображаемую сцену.
Пример:

```python3
s = box(10, center=True)
controller = disp(s)
nulltime = time.time()

def animate(widget):
	trans = rotateZ(time.time() - nulltime) * right(30)
	controller.set_location(trans)

show(animate=animate) 
```

Здесь мы используем специальную функцию анимации `animate`, которая, используя объект контроллер, возвращенный функцией disp, в зависимости от текущего момента времени обновляет местоположение контролируемого объекта.
В качестве параметра метода `set_location` выступает объект преобразования. (Подробнее в [Преобразования](trans0.html), [Комбинации преобразований](trans1.html))
