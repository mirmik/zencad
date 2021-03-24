# Линии и циклы.

Во многих случаях объёмных и плоских примитивов недостаточно для построения требуемой геометрии. Продвинутые операции, из числа тех, что встречаются в данном руководстве позволяют строить геометрические тела на основе произвольных линий.

В _ZenCad_ (и геометрическом ядре opencascade) существует два класса одномерных геометрических тел - _Edge_ и _Wire_. _Edge_ является простым примитивом. Объединение нескольких Edge в одну составную кривую порождают объект Wire. Как правило, в _ZenCad_, _Wire_ и _Edge_ могут использоваться взаимозаменяемо, однако при анализе модели с использованием рефлексии эта разница может быть существенной.")

Набор _Wire_ и/или _Edge_ может быть соединён в сложную кривую с помощью функции _sew_ (Подробнее ниже в этом разделе).

Замкнутые кривые называются циклами. Если кривая (все составные кривые) цикла лежит в одной плоскости, то такой цикл может быть преобразован в грань (Face) при помощи функции _fill_ (см. раздел "Плоские примитивы".).

Некоторые дополнительные операции при работе с кривыми описаны в разделе "Анализ кривых".

---
## Cегмент.
Отрезок обыкновенный, задаётся двумя точками.

Сигнатура:
```python
segment(pnt1, pnt2)
```
![](../images/generic/segment0.png)

---
## Полисегмент.
Полисегмент - ломанная линия. Задаётся масивом точек. Установка флага `closed` добавляет сегмент полилинии, идущий от точки конца к точке начала. `pnts` - массив точек.

Сигнатура:
```python
polysegment(pnts, closed=True/False)
```
![](../images/generic/polysegment0.png)
![](../images/generic/polysegment1.png)  

---
## Интерполяция по точкам.
Инструмент для построения интерполированной кривой, проходящей через набаор точек _pnts_. С помощью необязательного параметра _tangs_ в каждой точке можно задать направление, под которым кривая пройдёт через точку (нулевой вектор соответствует произвольному пересечению). Установка флага `closed` добавляет замыкающий участок кривой.

Сигнатура:
```python
interpolate(pnts, tangs=[], closed=False)
```
![](../images/generic/interpolate0.png)
![](../images/generic/interpolate1.png)  
![](../images/generic/interpolate2.png)
![](../images/generic/interpolate3.png)  


---
## Дуга окружности по трём точкам.
Данный метод представляет альтернативный к _circle_ (см. [Плоские примитивы](prim2d.html)) метод генерации дуги окружности по трем точкам.
Сигнатура:
```python
circle_arc(p1, p2, p3) 
```
![](../images/generic/circle_arc0.png)

---
## Восходящая спираль.
Восходящая спираль. Задается радиусом _r_, высотой _h_ и шагом витка _step_. При установке опции _left_, меняет правую навивку на левую. При установке необязательно параметра _angle,_ радиус меняется со сменой высоты по коническому закону.

Сигнатура:
```python
helix(r, h, step, angle=angle, left=True/False)
```
![](../images/generic/helix0.png)
![](../images/generic/helix1.png)  
![](../images/generic/helix2.png)
![](../images/generic/helix3.png)  

---
## Кривая Безье.
Кривая Безье ([wiki](https://en.wikipedia.org/wiki/B%C3%A9zier_curve)).
Задаётся массивом опорных точек и массивом весов (опционально).
Если веса не заданы, все веса считаются равными единице.

Сигнатура:
```python
bezier(pnts)
bezier(pnts, weights)
```
![](../images/generic/bezier0.png)
![](../images/generic/bezier1.png)  

---
## BSpline.
Создать BSpline прямым заданием параметров.

Сигнатура:
```python
bspline(pnts, knots, muls, degree, periodic=False/True)
bspline(pnts, knots, weights, muls, degree, periodic=False/True, check_rational=False/True)

default: 
	periodic=False
	check_rational=True
```
![](../images/generic/bspline0.png)
![](../images/generic/bspline1.png) 

---
## Скруглённый полисегмент.
В отличие от полисегмента, создаёт участки окружности в точках сопрежения сегментов. Переменная _r_ задаёт радиус скруглений. Может использоваться вместе с операцией tube (см. кинематические поверхности). 

Сигнатура:
```python
rounded_polysegment(pnts, r)
```

Пример:
```python
rounded_polysegment(
	pnts=[(0,0,0), (20,0,0), (20,20,40), (-40,20,40), (-40,20,0)], 
	r=10)
```

![](../images/generic/rounded_polysegment0.png)


---
## Создание сложной кривой. (sew)
Операция _sew_ собирает сложную линию из массива частей _wires_. 

В качестве элементов массива _wires_ могут выступать объекты типов Edge и Wire ([см. геометрические типы](https://mirmik.github.io/zencad/ru/geomcore.html)) 

Требования. Части линии обязательно должны граничить друг с другом. Порядок следования не должен быть нарушен. Если аргумент _sort_ установлен, алгоритм постарается автоматически отсортировать входящие линии в правильном порядке.

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
# Конструктор сложной кривой
Инструмент для последовательного конструирования участков кривой. Выполняя операции, конструирует рёбра от выходной точки предыдущего ребра. Каждая операция может быть выполнена в абсолютном и относительном режимах. В относительном режиме координаты опорных точек складываются с последней текущей координатой конструктора. Выбор режима осуществляется флагом _rel_. False - абсолютный, True - относительный. Если флаг не объявлен, используется значение _defrel_.

Аргументы конструктора:
_start_ - начальная точка
_defrel_ - режим по умолчанию

```python
wb = wire_builder(start=(0,0,0), defrel=False)
``` 

---
### Реинициализация:
Перезагрузка инструмента с новой точки. Сбрасывает список рёбер.
```python
wb.restart(pnt, y=None, z=None)
```

```python
wb.restart(point3(10,15,0))
wb.restart(10,15)
```

---
### Построение отрезка:
Строит отрезок до точки _pnt_. 
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
### Построение дуги окружности по точкам:
```python
wb.arc_by_points(a,b,rel=None)
```

---
### Построение интерполяционной кривой по точкам:
_curtang_ позволяет задать направление кривой в стартовой точке.
Установка опции _approx_ вычисляет _curtang_ в значение направления кривой в конце прошлого участка.  
```python
wb.interpolate(pnts, tangs=None, curtang=(0,0,0), approx=False, rel=None)
```

## Замыкание
_сlose_ строит участок кривой до точки старта. _approx\_a_, _approx\_b_ позволяют сделать интерполяцию в точках замыкания.

```python
wb.close(approx_a=False, approx_b=False)
```