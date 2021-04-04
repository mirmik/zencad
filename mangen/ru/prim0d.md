:ru
# Точка, вектор, вспомогательные функции.

В библиотеки ZenCad есть некоторые вспомогательные математические объекты и функции для работы с ними.
:en
# Point, vector, helper functions.

ZenCad has some math helpers and functions for working with them.
::

---
:ru
## Точка
Некоторые функции ZenCad используют в качестве параметров точки или массивы точек. Для создания объекта точки можно использовать функцию `point3`. Кроме того, часто функция может сама сформировать точки по списку или кортежу координат.
:en
## Point
Some ZenCad functions use points or point arrays as parameters. You can use the `point3` function to create a point object. In addition, often a function can itself form points from a list or a tuple of coordinates. 
::

```python
point3(0,3,6)

#Equivalent calls
interpolate([point3(0,0,0), point3(0,0,10), point3(10,0,10)])
interpolate([(0,0,0), (0,0,10), (10,0,10)])
interpolate(points([(0,0,0), (0,0,10), (10,0,10)]))
```

:ru
Точка может быть отображена функцией display, как соответствующая такой точке вершина.
:en
A point can be displayed with the display function as the corresponding vertex for such a point.
::

---
:ru
## Вектор
Иногда кроме указаний точек используются объекты-векторы для указания направлений. Принцип работы с векторами аналогичен работе с точками.
:en
## Vector
Sometimes, in addition to specifying points, vector objects are used to indicate directions. The principle of working with vectors is similar to working with points.
::

```python
vector3(1,2,3)

interpolate(pnts=[(0,0,0), (0,0,10), (10,0,10)], tangs=[(0,0,1), (1,0,0), (0,1,0)])
```

:ru
Вектор не может быть отображен непосредственно.  
В отличии от точки вектор игнорирует трансляцию при преобразованиях.
:en
The vector cannot be displayed directly.
Unlike a point, a vector ignores translation during transformations.
::

---
:ru
## Масивы точек и векторов
Функции vectors и points явно создают массивы точек из массивов координат.
points2 создаёт двумерный массив точек из двумерного списка.
:en
## Point and vector arrays
The vectors and points functions explicitly create arrays of points from arrays of coordinates.
points2 creates a two-dimensional array of points from a two-dimensional list.
::

```python
points([(0,0,0), (0,0,10), (10,0,10)])
vectors([(0,0,1), (1,0,0), (0,1,0)])

points2([
	[(0,0,0), (0,0,10), (10,0,10)],
	[(1,6,0), (0,5,10), (10,5,10)]
])
```

---
:ru
## Инкрементальный масив точек
Создаёт массив точек на основе смещений.
:en
## Incremental array of points
Creates an array of points based on offsets.
::
```python
points_incremental([(0,2,0), (0,0,10), (5,0,0), (5,0,0)])
# Создаёт масив точек:
# (0,2,0)
# (0,2,10)
# (5,2,10)
# (10,2,10)
```

---
:ru 
## Операции над точками и векторами
Точки и вектора могут использоваться в математических операциях в соответствиями с правилами линейной алгебры.
:en
## Operations on points and vectors
Points and vectors can be used in mathematical operations according to the rules of linear algebra.
::

```python
pnt - pnt -> vec
pnt + vec -> pnt
vec + vec -> vec
vec - vec -> vec
```

---
:ru
## Пустое примитив. nullshape
Пустой примитив. Может участвовать в булевых операциях.  

Пример использования в цикле:
:en
## Empty primitive. nullshape
Empty primitive. Can participate in boolean operations.

An example of use in a loop:
::
```python
it = nullshape()
for i in range(7):
	it = it + box(20).translate(10*i,10*i,10*i)

#alternate: union([box(20).translate(10*i,10*i,10*i) for i in range(7)])
```

---
:ru
## Перевод угловых величин. Радианы и градусы
API zencad использует радианы для задания углов. Использование градусов требует масштабирования численного коэффициента. Именно этим и занимается функция deg (синоним deg2rad):  
`deg(180)` соответствует `math.pi`.

Обратное преобразование выполняется функцией rad2deg.
:en
## Conversion of angular values. Radians and degrees
The zencad API uses radians to define angles. Using degrees requires scaling a numerical factor. This is exactly what the deg function does (synonymous with deg2rad):
`deg (180)` matches `math.pi`.

The reverse conversion is performed by the rad2deg function.
::

Сигнатуры:
```python
# Convert degrees to radians:
def deg2rad(grad)
def deg(grad)

# Convert radians to degrees:
def rad2deg(rad)
```

:ru
Код функции deg2rad, rad2deg:
:en
Function code deg2rad, rad2deg:
::
```python
def deg2rad(grad):
    return float(grad) / 180.0 * math.pi

def rad2deg(rad):
    return float(rad) * 180.0 / math.pi
```

Пример:
```python
rotateZ(deg(45))
```

---
:ru
### Зарегистрировать шрифт
Регистрирует в системе шрифт в формате FreeType.
:en
### Register font
Register FreeType font in system.
:end

```python
register_font(fontpath) 
```