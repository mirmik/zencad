# Отображение

## Display
Функция display добавляет объект в сцену по умолчанию.

```python
display(model)
display(model, color)
display(listOfModels)
display(listOfModels, color)

disp(model)
etc...
```

## Scene
Scene - это контейнер, хранящий модели и закреплённые за ними цвета. 

```python
scene = Scene()
scene.add(model)
scene.add(model, color)
``` 

## Color
Объект, содержащий информацию о цвете в формате rgba. Диапазон значений параметров [0,1].
```python
color(r,g,b,a)
```

## Show
Функция show инициирует отображение программы визуализатора. Если функция вызывается без аргументов, отображается сцена по умолчанию.

```python
show()
show(scene)
``` 