:ru
# Линии и циклы.

Во многих случаях объёмных и плоских примитивов недостаточно для построения требуемой геометрии. Продвинутые операции, из числа тех, что встречаются в данном руководстве позволяют строить геометрические тела на основе произвольных линий.

В _ZenCad_ (и геометрическом ядре opencascade) существует два класса одномерных геометрических тел - _Edge_ и _Wire_. _Edge_ является простым примитивом. Объединение нескольких Edge в одну составную кривую порождают объект Wire. Как правило, в _ZenCad_, _Wire_ и _Edge_ могут использоваться взаимозаменяемо, однако при анализе модели с использованием рефлексии эта разница может быть существенной.")

Набор _Wire_ и/или _Edge_ может быть соединён в сложную кривую с помощью функции _sew_ (Подробнее ниже в этом разделе).

Замкнутые кривые называются циклами. Если кривая (все составные кривые) цикла лежит в одной плоскости, то такой цикл может быть преобразован в грань (Face) при помощи функции _fill_ (см. раздел "Плоские примитивы".).

Некоторые дополнительные операции при работе с кривыми описаны в разделе "Анализ кривых".
:en
# Lines and loops.

In many cases, three-dimensional and flat primitives are not enough to build the required geometry. Advanced operations, from among those that are found in this tutorial, allow you to create geometric bodies based on arbitrary lines.

In _ZenCad_ (and the opencascade geometric kernel), there are two classes of one-dimensional geometric solids - _Edge_ and _Wire_. _Edge_ is a simple primitive. Combining multiple Edges into a single compound curve results in a Wire object. Typically, _ZenCad_, _Wire_, and _Edge_ can be used interchangeably, but when analyzing a model using reflection, this difference can be significant. ")

The _Wire_ and / or _Edge_ set can be connected to a complex curve using the _sew_ function (More details later in this section).

Closed curves are called cycles. If the curve (all compound curves) of the cycle lies in the same plane, then such a cycle can be converted into a face (Face) using the _fill_ function (see the section "Plane primitives".).

Some additional operations when working with curves are described in the "Curve Analysis" section.
::

---
:ru
## Сегмент
Отрезок обыкновенный, задаётся двумя точками.
:en
## Segment
An ordinary segment, specified by two points.
::

Сигнатура:
```python
segment(pnt1, pnt2)
```
![](../images/generic/segment0.png)

---
:ru
## Полисегмент
Полисегмент - ломанная линия. Задаётся масивом точек. Установка флага `closed` добавляет сегмент полилинии, идущий от точки конца к точке начала. `pnts` - массив точек.
:en
## Polysegment
Polysegment is a broken line. Set by an array of points. Setting the closed flag adds a polyline segment from the end point to the start point. `pnts` is an array of points.
::

Сигнатура:
```python
polysegment(pnts, closed=True/False)
```
![](../images/generic/polysegment0.png) ![](../images/generic/polysegment1.png)  

---
:ru
## Интерполяция по точкам
Инструмент для построения интерполированной кривой, проходящей через набаор точек _pnts_. С помощью необязательного параметра _tangs_ в каждой точке можно задать направление, под которым кривая пройдёт через точку (нулевой вектор соответствует произвольному пересечению). Установка флага `closed` добавляет замыкающий участок кривой.
:en
## Point Interpolation
Tool for constructing an interpolated curve passing through a set of _pnts_ points. Using the optional _tangs_ parameter at each point, you can set the direction in which the curve will pass through the point (the zero vector corresponds to an arbitrary intersection). Setting the `closed` flag adds a trailing portion of the curve. 
::

Сигнатура:
```python
interpolate(pnts, tangs=[], closed=False)
```
![](../images/generic/interpolate0.png) ![](../images/generic/interpolate1.png) </br>
![](../images/generic/interpolate2.png) ![](../images/generic/interpolate3.png)

---
:ru
## Дуга окружности по трём точкам
Данный метод представляет альтернативный к _circle_ (см. [Плоские примитивы](prim2d.html)) метод генерации дуги окружности по трем точкам.
:en
## Arc of a circle with three points
This method represents an alternative to _circle_ (see [Plane Primitives](prim2d.html)) method of generating a circular arc from three points. 
::

Сигнатура:
```python
circle_arc(p1, p2, p3) 
```
![](../images/generic/circle_arc0.png)

---
:ru
## Восходящая спираль
Восходящая спираль. Задается радиусом _r_, высотой _h_ и шагом витка _step_. При установке опции _left_, меняет правую навивку на левую. При установке необязательно параметра _angle_, радиус меняется со сменой высоты по коническому закону.
:en
## Upward spiral
An upward spiral. It is set by the radius _r_, the height _h_ and the step of the loop _step_. When setting the option _left_, it changes the right winding to the left one. When setting the optional parameter _angle_, the radius changes with the change of height according to the conical law. 
::

Сигнатура:
```python
helix(r, h, step, angle=angle, left=True/False)
```
![](../images/generic/helix0.png) ![](../images/generic/helix1.png) </br>
![](../images/generic/helix2.png) ![](../images/generic/helix3.png)

---
:ru
## Кривая Безье
Кривая Безье ([wiki](https://en.wikipedia.org/wiki/B%C3%A9zier_curve)).
Задаётся массивом опорных точек и массивом весов (опционально).
Если веса не заданы, все веса считаются равными единице.
:en
## Bezier Curve
Bezier curve ([wiki](https://en.wikipedia.org/wiki/B%C3%A9zier_curve)).
Defined by an array of control points and an array of weights (optional).
If weights are not specified, all weights are considered equal to one. 
::

Сигнатура:
```python
bezier(pnts)
bezier(pnts, weights)
```
![](../images/generic/bezier0.png) ![](../images/generic/bezier1.png)  

---
## BSpline
:ru
Создать BSpline прямым заданием параметров.
:en
::

Сигнатура:
```python
bspline(pnts, knots, muls, degree, periodic=False/True)
bspline(pnts, knots, weights, muls, degree, periodic=False/True, check_rational=False/True)

default: 
	periodic=False
	check_rational=True
```
![](../images/generic/bspline0.png) ![](../images/generic/bspline1.png) 

---
:ru
## Скруглённый полисегмент
В отличие от полисегмента, создаёт участки окружности в точках сопряжения сегментов. Переменная _r_ задаёт радиус скруглений. Может использоваться вместе с операцией tube (см. кинематические поверхности). 
Опция closed позволяет замкнуть кривую с созданием скруглённого сегмента на стыке.
:en
## Rounded polysegment
Unlike a polysegment, it creates sections of a circle at the mating points of the segments. The _r_ variable sets the radius of the fillets. Can be used in conjunction with the tube operation (see kinematic surfaces).
The closed option allows you to close the curve and create a rounded segment at the junction. 
::

Сигнатура:
```python
rounded_polysegment(pnts, r, closed=False)
```

Пример:
```python
rounded_polysegment(
	pnts=[(0,0,0), (20,0,0), (20,20,40), (-40,20,40), (-40,20,0)], 
	r=10)
```

![](../images/generic/rounded_polysegment0.png)


---
:ru
## Создание сложной кривой
Операция _sew_ собирает сложную линию из массива частей _wires_. 

В качестве элементов массива _wires_ могут выступать объекты типов Edge и Wire ([см. геометрические типы](https://mirmik.github.io/zencad/ru/geomcore.html)) 

Требования. Части линии обязательно должны граничить друг с другом. Порядок следования не должен быть нарушен. Если аргумент _sort_ установлен, алгоритм постарается автоматически отсортировать входящие линии в правильном порядке.
:en
## Creating a complex curve
The _sew_ operation assembles a complex line from an array of _wires_ pieces.

Objects of types Edge and Wire can act as elements of the _wires_ array ([see geometric types](https://mirmik.github.io/zencad/ru/geomcore.html))

Requirements. Parts of the line must necessarily border on each other. The order should not be out of order. If the _sort_ argument is set, the algorithm will try to automatically sort the incoming lines in the correct order. 
::

Сигнатура:
```python
sew(wires, [sort=True])
```

Пример:
```python
sew([
	segment((0,0,0), (0,10,0)), 
	circle_arc((0,10,0),(10,15,0),(20,10,0)), 
	segment((20,0,0), (20,10,0)),
	segment((20,0,0), (0,0,0))
])
```
![](../images/generic/fill0.png)



---
:ru 
# Конструктор сложной кривой
Инструмент для последовательного конструирования участков кривой. Выполняя операции, конструирует рёбра от выходной точки предыдущего ребра. Каждая операция может быть выполнена в абсолютном и относительном режимах. В относительном режиме координаты опорных точек складываются с последней текущей координатой конструктора. Выбор режима осуществляется флагом _rel_. False - абсолютный, True - относительный. Если флаг не объявлен, используется значение _defrel_.

Аргументы конструктора:
_start_ - начальная точка
_defrel_ - режим по умолчанию
:en
# Complex curve constructor
Tool for sequential construction of curve sections. Performing operations, constructs edges from the exit point of the previous edge. Each operation can be performed in absolute and relative modes. In relative mode, the coordinates of the anchor points are added to the last current coordinate of the constructor. The choice of the mode is carried out by the _rel_ flag. False is absolute, True is relative. If no flag is declared, the _defrel_ value is used.

Constructor arguments:
_start_ - starting point
_defrel_ - default mode 
::

```python
wb = wire_builder(start=(0,0,0), defrel=False)
``` 

---
:ru
### Реинициализация:
Перезагрузка инструмента с новой точки. Сбрасывает список рёбер.
:en
### Reinitialization:
Reloads the instrument from a new point. Resets the list of edges. 
::
```python
wb.restart(pnt, y=None, z=None)
```

```python
wb.restart(point3(10,15,0))
wb.restart(10,15)
```

---
:ru
### Построение отрезка:
Строит отрезок до точки _pnt_. 
:en
### Drawing a line segment:
Draws a segment to the point _pnt_. 
::
```python
wb.segment(pnt, y=None, z=None, rel=None)
wb.line(b, y=None, z=None, rel=None)
wb.l(b, y=None, z=None, rel=None)

```

```python
wire_builder(defrel=True).restart((0,10)).l(10,0).l(0,-10).close().doit() # рисуем квадрат
```
![](../images/generic/wb_segment0.png)

-----
:ru
### Построение дуги окружности по точкам:
:en
### Draw a circular arc by points: 
::
```python
wb.arc_by_points(a,b,rel=None)
```


---
:ru
### Построение интерполяционной кривой по точкам:
_curtang_ позволяет задать направление кривой в стартовой точке.
Установка опции _approx_ вычисляет _curtang_ в значение направления кривой в конце прошлого участка.  
:en
### Plotting an interpolation curve by points:
_curtang_ allows you to set the direction of the curve at the starting point.
Setting the _approx_ option calculates _curtang_ to the direction of the curve at the end of the last leg.
::
```python
wb.interpolate(pnts, tangs=None, curtang=(0,0,0), approx=False, rel=None)
```

:ru
### Замыкание
_сlose_ строит участок кривой до точки старта. _approx\_a_, _approx\_b_ позволяют сделать интерполяцию в точках замыкания.
:en
### Closure
_close_ builds a section of the curve up to the starting point. _approx\_a_, _approx\_b_ allow for interpolation at snapping points.
::

```python
wb.close(approx_a=False, approx_b=False)
```