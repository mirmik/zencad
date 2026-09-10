# Топология и селекторы

Геометрические объекты состоят из более простых компонентов: тел, граней, рёбер и вершин. Подробнее — в [описании BREP](geomcore.html).

## Получение компонентов

Методы возвращают коллекции `ShapeList` с соответствующим типом элементов:

```python
shape.vertices() # -> ShapeList[Vertex]
shape.solids() # -> ShapeList[Solid]
shape.faces() # -> ShapeList[Face]
shape.edges() # -> ShapeList[Edge]
shape.wires() # -> ShapeList[Wire]
shape.shells() # -> ShapeList[Shell]
shape.compounds() # -> ShapeList[Compound]
shape.compsolids() # -> ShapeList[CompSolid]
```

Координаты вершины доступны через `vertex.point()`. Индексирование, срезы, фильтры и сортировка сохраняют граф вычислений; `len()`, итерация, `geometry_types()` и `group_by()` вычисляют коллекцию.

## Выбор элементов

```python
import zencad as z

body = z.box(20, 20, 30, center="xy")
vertical = body.edges().filter_by(z.Axis.Z)
rounded = z.fillet(body, 2, vertical)
side_faces = body.faces().filter_by_position(z.Axis.Z, 15)
tapered = z.draft(body, side_faces, z.deg(5))
top = body.faces().planar().sort_by(z.Axis.Z)[-1]
assert len(side_faces) == 4
assert abs(float(top.center().z) - 30) < 1e-7
rounded.assert_valid()
tapered.assert_valid()
```

| Запрос | Значение |
| --- | --- |
| `filter_by(GeomType.PLANE)` / `planar()` | Плоские поверхности |
| `normal_to(Axis.Z)` | Плоские грани с нормалью параллельно Z, обоих знаков |
| `filter_by_position(Axis.Z, z)` | Центр на заданной высоте |
| `filter_by(Plane.xy(z))` | Центр на указанной плоскости |
| `sort_by(Axis.Z)` | Порядок по проекции центра |
| `sort_by_distance(point)` | Порядок по минимальному расстоянию до формы |
| `longer_than(length)` | Рёбра/проволоки с большей длиной |
| `largest()` | Наибольшая длина, площадь или объём по типу формы |
| `only()` | Ровно один элемент, иначе ошибка при вычислении |

Индекс не закреплён за конкретной гранью: после изменения модели порядок может измениться. Предпочитайте выбор по геометрическим свойствам.

`fillet` и `chamfer` принимают рёбра, `draft` — грани. Подробнее: [контракт селекторов](../development/topology-selectors.md).

## Ближайший элемент

Функции возвращают компонент формы `shp`, ближайший к точке `pnt`:

```python
near_edge(shp, pnt) # -> Edge
near_face(shp, pnt) # -> Face
near_vertex(shp, pnt) # -> Vertex; .point() -> Point3
```

## Проверка состава и восстановление типа

Проверка отсутствия тел (грани и рёбра при этом могут присутствовать):

```python
len(shp.solids()) == 0
```

`restore_shapetype` извлекает единственный подходящий компонент формы. Если нужен ровно один solid, используйте `shp.solids().only()`.

```python
original_shp = restore_shapetype(shp)
```
