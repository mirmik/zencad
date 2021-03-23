:ru
# Ограничивающая коробка

Ограничивающая коробка - это это минимальный основанный на осях Ox, Oy, Oz параллелепипед, описывающий геометрическую форму shape.
:en
# Bounding box

The bounding box is a minimal Ox, Oy, Oz-based box that describes the geometric shape shape. 
::

---
:ru
## shape.bbox
Построить ограничивающую коробку на основе формы shape.
:en
## shape.bbox
Construct a bounding box based on the shape. 
::

Пример
```python
shp = sphere(10)
bbox = shp.bbox()
```

:ru
## Поля.
:en
## Fields. 
::
```python3
bbox.xmin
bbox.ymin
bbox.zmin
bbox.xmax
bbox.ymax
bbox.zmax
```

:ru
## Методы.
:en
## Methods.
::
bbox.xrange()
bbox.yrange()
bbox.zrange()

:ru
## Построить коробку как форму.
:en
## To Shape.
::
Пример
```python
shp = sphere(10)
bbox = shp.bbox()
disp(bbox.shape())
```
