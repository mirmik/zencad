# Операции генерации линий.
Линии могут использоваться как части составных граней (см. операции `sew` и `fill`), а также как аргументы для операций ссылочной геометрии. 

---
## Segment
Отрезок линии задаётся двумя точками.
```python
segment(pnt1, pnt2)
```
![](../images/generic/segment0.png)

---
## Polysegment
Полисегмент - ломанная линия. Задаётся масивом точек. Установка флага `closed` добавляет сегмент полилинии, идущий от точки конца к точке начала. `pnts` - массив точек.
```python
polysegment(pnts, closed=True/False)
```
![](../images/generic/polysegment0.png)
![](../images/generic/polysegment1.png)  

---
## Interpolate
Инструмент для построения bspline по набору точек `pnts`. Также можно указать тангенсы `tangs` линии в каждой точке (нулевой мектор соответствует неуказанному тангенсу). Установка флага `closed` добавляет замыкающий участок кривой.
```python
interpolate(pnts, tangs=[], closed=False):
```
![](../images/generic/interpolate0.png)
![](../images/generic/interpolate1.png)  
![](../images/generic/interpolate2.png)
![](../images/generic/interpolate3.png)  


---
## Circle Arc
Данный метод представляет альтернативный к `circle` (см. [Плоские примитивы](prim2d.html)) метод генерации дуги окружности по трем точкам.
```python
circle_arc(p1, p2, p3) 
```
![](../images/generic/circle_arc0.png)

---
## Helix
Восходящая спираль. Задается радиусом, высотой и шагом витка. При установке опции `left`, меняет правую навивку на левую. При установке angle, радиус линейно меняется со сменой высоты.

```python
helix(r, h, step, left=True/False):
helix(r, h, step, angle=angle, left=True/False):
```
![](../images/generic/helix0.png)
![](../images/generic/helix1.png)  
![](../images/generic/helix2.png)
![](../images/generic/helix3.png)  