:ru
# Топология и селекторы

`vertices()`, `edges()`, `faces()` и другие запросы возвращают `ShapeList[T]`. Индекс, срез, фильтр и сортировка создают выражение; `len()`, итерация, `geometry_types()` и `group_by()` материализуют коллекцию.

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

Топологические запросы упорядочены лексикографически по центру X/Y/Z с округлением до девяти знаков. Это не постоянные идентификаторы топологии: после правки модели выбранный индекс может обозначать другую грань. При равных ключах сохраняется исходный порядок. Для моделирования предпочитайте геометрический критерий.

`fillet` и `chamfer` принимают выбранные рёбра, `draft` — выбранные грани. Повторные вхождения одного ребра дедуплицируются перед построением; чужие рёбра вызывают ошибку. Подробный контракт: [Topology selectors](../development/topology-selectors.md).
:en
# Topology and selectors

`vertices()`, `edges()`, `faces()` and other queries return `ShapeList[T]`. Indexing, slicing, filtering and sorting construct expressions; `len()`, iteration, `geometry_types()` and `group_by()` materialize collections.

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

| Query | Meaning |
| --- | --- |
| `filter_by(GeomType.PLANE)` / `planar()` | Planar surfaces |
| `normal_to(Axis.Z)` | Planar faces with normals parallel to Z, either sign |
| `filter_by_position(Axis.Z, z)` | Center at the specified height |
| `filter_by(Plane.xy(z))` | Center on the specified plane |
| `sort_by(Axis.Z)` | Sort by center projection |
| `sort_by_distance(point)` | Sort by minimum shape-to-point distance |
| `longer_than(length)` | Edges/wires with greater length |
| `largest()` | Greatest length, area or volume for the shape type |
| `only()` | Exactly one element, otherwise an evaluation error |

Topology queries sort lexicographically by center X/Y/Z, rounded to nine decimal places. These are not persistent topology identities: an index can select another face after a model edit. Equal keys retain input order. Prefer geometric criteria for modeling.

`fillet` and `chamfer` accept selected edges; `draft` accepts selected faces. Repeated occurrences of an edge are deduplicated before building; foreign edges cause an error. Full contract: [Topology selectors](../development/topology-selectors.md).
::
