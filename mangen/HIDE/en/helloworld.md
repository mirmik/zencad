# Привет, друг.

Вот пример, демонстрирующий принцип построения моделей в zencad.
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
## Что происходит:
```python
from zencad import *
```
В первой строчке мы импортируем в текущее пространство пространство имён zencad. В данном случае, нас интересуют функции `box`, `sphere`, `display`, `show`.
</br>
</br>


```python
a = box(200, 200, 200, center = True)
b = sphere(120)
c = sphere(60)
```
Подготавливаем геометрические примитивы. Создаётся объект box с размерами 200x200x200 и смещением геометрического центра в начало координат. Также создаются две сферы радиусом 120 и 60.
</br>
</br>


```python
model = a - b + c
```
Вычисляем модель с применением булевых операций. Сперва из куба будет вычтена большая сфера. Потом добавлена малая. Порядок слагаемых в данном случае важен, поскольку операции объединения и разности геометрических тел некомутативны.
</br>
</br>


```python
display(model)
```
Функция display передаёт объект в сцену для последующего отображения.
</br>
</br>


```python
show()
```
Отображаем виджет сцены.

---------------------------
## Если всё прошло благополучно:
![](../images/helloworld.png)