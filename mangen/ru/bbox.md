# Ограничивающая коробка

Ограничивающая коробка - это это минимальный основанный на осях Ox, Oy, Oz параллелепипед, описывающий геометрическую форму shape.

---
## shape.bbox
Построить ограничивающую коробку на основе формы shape.

Пример
```python
shp = sphere(10)
bbox = shp.bbox()
```

## Поля
```python3
bbox.xmin
bbox.ymin
bbox.zmin
bbox.xmax
bbox.ymax
bbox.zmax
```

## Методы
bbox.xrange()
bbox.yrange()
bbox.zrange()

## Построить коробку как форму
Пример
```python
shp = sphere(10)
bbox = shp.bbox()
disp(bbox.shape())
```
