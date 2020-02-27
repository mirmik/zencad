# Кривые и циклы.

Во многих случаях объёмных и плоских примитивов недостаточно для построения требуемой геометрии. Продвинутые операции, из числа тех, что встречаются в данном руководстве позволяют строить геометрические тела на основе произвольных линий.

В _ZenCad_ (и геометрическом ядре opencascade) существует два класса одномерных геометрических тел - _Edge_ и _Wire_. _Edge_ является простым примитивом. Объединение нескольких Edge в одну составную кривую порождают объект Wire. Как правило, в _ZenCad_, _Wire_ и _Edge_ могут использоваться взаимозаменяемо, однако при анализе модели с использованием рефлексии эта разница может быть существенной.")

Набор _Wire_ и/или _Edge_ может быть соединён в сложную кривую с помощью функции _sew_ (Подробнее ниже в этом разделе).

Замкнутые кривые называются циклами. Если кривая (все составные кривые) цикла лежит в одной плоскости, то такой цикл может быть преобразован в грань (Face) при помощи функции _fill_ (см. раздел "Плоские примитивы".).

Некоторые дополнительные операции при работе с кривыми описаны в разделе "Анализ кривых".

---
## segment
Отрезок линии задаётся двумя точками.
```python
segment(pnt1, pnt2)
```
![](../images/generic/segment0.png)

---
## polysegment
Полисегмент - ломанная линия. Задаётся масивом точек. Установка флага `closed` добавляет сегмент полилинии, идущий от точки конца к точке начала. `pnts` - массив точек.
```python
polysegment(pnts, closed=True/False)
```
![](../images/generic/polysegment0.png)
![](../images/generic/polysegment1.png)  

---
## interpolate
Инструмент для построения bspline по набору точек `pnts`. Также можно указать тангенсы `tangs` линии в каждой точке (нулевой мектор соответствует неуказанному тангенсу). Установка флага `closed` добавляет замыкающий участок кривой.
```python
interpolate(pnts, tangs=[], closed=False)
```
![](../images/generic/interpolate0.png)
![](../images/generic/interpolate1.png)  
![](../images/generic/interpolate2.png)
![](../images/generic/interpolate3.png)  


---
## circle_arc
Данный метод представляет альтернативный к `circle` (см. [Плоские примитивы](prim2d.html)) метод генерации дуги окружности по трем точкам.
```python
circle_arc(p1, p2, p3) 
```
![](../images/generic/circle_arc0.png)

---
## helix
Восходящая спираль. Задается радиусом, высотой и шагом витка. При установке опции `left`, меняет правую навивку на левую. При установке angle, радиус линейно меняется со сменой высоты.

```python
helix(r, h, step, left=True/False)
helix(r, h, step, angle=angle, left=True/False)
```
![](../images/generic/helix0.png)
![](../images/generic/helix1.png)  
![](../images/generic/helix2.png)
![](../images/generic/helix3.png)  

---
## bezier
Кривая Безье ([wiki](https://en.wikipedia.org/wiki/B%C3%A9zier_curve)).
Задаётся массивом опорных точек и массивом весов (опционально).
Если веса не заданы, все веса считаются равными единице.
```python
bezier(pnts)
bezier(pnts, weights)
```
![](../images/generic/bezier0.png)
![](../images/generic/bezier1.png)  

---
## bspline
Создать BSpline прямым заданием параметров.
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
## Sew
Операция _sew_ собирает сложную линию из массива частей _wires_. 

В качестве элементов массива _wires_ могут выступать объекты типов Edge и Wire ([см. геометрические типы](https://mirmik.github.io/zencad/ru/geomcore.html)) 

Требования. Части линии обязательно должны граничить друг с другом. Порядок следования не должен быть нарушен. Если аргумент _sort_ установлен, алгоритм постарается автоматически отсортировать входящие линии в правильном порядке.

```python
sew(wires, [sort=True])

# Example:
sew([
	segment((0,0,0), (0,10,0)), 
	circle_arc((0,10,0),(10,15,0),(20,10,0)), 
	segment((20,0,0), (20,10,0)),
	segment((20,0,0), (0,0,0))
])
```
![](../images/generic/fill0.png)
