:ru
# Прочие операции.

В этом разделе перечислены операции не подходящие ни к одному другому разделу.

---
## unify
Данная операция упрощает геометрическое представление объекта, путём удаления лишних рёбер и объединения гранией.

Может выполняться над двумерными и трёхмерными объектами.
:en
# Other operations.

This section lists operations that do not fit into any other section.

---
## unify
This operation simplifies the geometric representation of an object by removing unnecessary edges and merging with a face.

Can be performed on 2D and 3D objects. 
::

Сигнатура:
```python
unify(shp)
```

Пример:
```python
unify(cylinder(r=10, h=10) + cylinder(r=10, h=10).move(5,5))
```
:ru
| До | После |
:en
| Before | After |
::
|---|---|
| ![](../images/generic/unify0.png) | ![](../images/generic/unify1.png) |
