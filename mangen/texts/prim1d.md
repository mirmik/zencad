# Операции генерации линий.
Линии могут использоваться как части составных граней (см. операции `sew` и `fill`), а также как аргументы для операций ссылочной геометрии. 

---
## Segment
Отрезок линии задаётся двумя точками.
```python
segment(pnt1, pnt2)
```
![](images/generic/segment0.png)

---
## Polysegment
Полисегмент - ломанная линия. Задаётся масивом точек. Установка флага closed добавляет сегмент полилинии, идущий от точки конца к точке начала. `pnts` - массив точек.
```python
polysegment(pnts, closed=True/False)
```
![](images/generic/polysegment0.png)
![](images/generic/polysegment1.png)

---
