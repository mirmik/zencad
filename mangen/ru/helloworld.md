:ru
# Привет, друг.

Вот пример, демонстрирующий принцип построения моделей в zencad.
:en
# Hello Friend.

Here is an example to demonstrate the principle of building models in zencad. 
::
```python
from zencad import *

a = box(200, 200, 200, center = True)
b = sphere(120)
c = sphere(60)

model = a - b + c

display(model)

show()
```

------------------
:ru
## Что происходит:
:en
## What's happening: 
::
```python
from zencad import *
```
:ru
В первой строчке мы импортируем в текущее пространство пространство имён zencad. В данном случае, нас интересуют функции `box`, `sphere`, `display`, `show`.
:en
In the first line, we import into the current zencad namespace. In this case, we are interested in the `box`,` sphere`, `display`,` show` functions. 
::
</br>
</br>


```python
a = box(200, 200, 200, center = True)
b = sphere(120)
c = sphere(60)
```
:ru
Подготавливаем геометрические примитивы. Создаётся объект box с размерами 200x200x200 и смещением геометрического центра в начало координат. Также создаются две сферы радиусом 120 и 60.
:en
Preparing geometric primitives. A box object is created with dimensions 200x200x200 and an offset of the geometric center to the origin. It also creates two spheres with a radius of 120 and 60. 
::
</br>
</br>


```python
model = a - b + c
```
:ru
Вычисляем модель с применением булевых операций. Сперва из куба будет вычтена большая сфера. Потом добавлена малая. Порядок слагаемых в данном случае важен, поскольку операции объединения и разности геометрических тел некомутативны.
:en
Computing the model using boolean operations. First, a large sphere will be subtracted from the cube. Then a small one was added. The order of the terms is important in this case, since the operations of union and difference of geometric bodies are non-commutative. 
::
</br>
</br>


```python
disp(model)
```
:ru
Функция `disp` передаёт объект в сцену для последующего отображения.
:en
The `disp` function passes the object into the scene for later display. 
::
</br>
</br>


```python
show()
```
:ru
Отображаем виджет сцены.
:en
Displaying the scene widget. 
::

---------------------------
:ru
## Если всё прошло благополучно:
:en
## If everything went well: 
::
![](../images/helloworld.png)
