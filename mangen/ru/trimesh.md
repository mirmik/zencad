:ru
# Триангуляция и mesh

`Shape.to_mesh()` возвращает типизированный `MeshData`, сохраняя граф формы. Материализованная запись содержит позиции, нормали, индексы треугольников, соответствие граням и число отброшенных треугольников.

```python
import zencad as z

mesh = z.box(10).to_mesh(0.5)
record = mesh.value()
assert record.vertex_count > 0
assert record.triangle_count > 0
arrays = mesh.to_numpy()
assert arrays.positions.shape[1] == 3
native = mesh.native()
```

`mesh.positions` и `mesh.triangles` дают численные кортежи, `.to_numpy()` — свежие изменяемые массивы, `.native()` — `Poly_Triangulation`. Это явные границы вычисления; изменение массива не меняет исходную форму. Mesh — приближение геометрии, не точный BREP. Для [STL/3MF](expimp.html) можно сразу вызвать экспорт без ручного построения сетки.
## Отображение сетки

```python
import zencad as z

model = z.torus(30, 8) - z.box(60, 12, 12, center=True)
mesh = model.to_mesh(linear_deflection=0.35)
z.display(mesh, color=z.orange, display_mode="shaded_with_edges")
z.show()
```

Просмотрщик отображает сетку напрямую, без преобразования каждого треугольника
в BREP-грань. Режимы отображения: `shaded_with_edges`, `shaded`, `wireframe`.
`linear_deflection` и `angular_deflection` задают детализацию; `crease_angle`
определяет границы, на которых нормали остаются раздельными.

## Полигедрон

`polyhedron(pnts, faces, shell=False)` строит форму из вершин и граней,
заданных индексами вершин. Для оболочки вместо тела задайте `shell=True`.

```python
import zencad as z

mesh = z.sphere(10).to_mesh(0.5)
model = z.polyhedron(mesh.positions, mesh.triangles)
z.display(model)
z.show()
```

![Полигедрон по триангуляции сферы](../images/generic/polyhedron0.png)

## Выпуклая оболочка

`convex_hull` вычисляет индексы граней выпуклой оболочки множества точек,
`convex_hull_shape` строит соответствующую форму. Требуется SciPy.
Параметры `incremental` и `qhull_options` передаются алгоритму SciPy;
`convex_hull_shape(..., shell=True)` создаёт оболочку вместо тела.

```python
import zencad as z

points = z.points([(0, 0, 0), (10, 0, 0), (10, 10, 0), (0, 10, 0), (5, 5, 10)])
model = z.convex_hull_shape(points)
z.display(model)
z.show()
```

![Выпуклая оболочка пяти точек](../images/generic/convex_hull0.png)
:en
# Triangulation and meshes

`Shape.to_mesh()` returns typed `MeshData`, retaining the shape graph. Its materialized record contains positions, normals, triangle indices, face IDs and the number of dropped triangles.

```python
import zencad as z

mesh = z.box(10).to_mesh(0.5)
record = mesh.value()
assert record.vertex_count > 0
assert record.triangle_count > 0
arrays = mesh.to_numpy()
assert arrays.positions.shape[1] == 3
native = mesh.native()
```

`mesh.positions` and `mesh.triangles` expose numeric tuples; `.to_numpy()` returns fresh mutable arrays; `.native()` returns `Poly_Triangulation`. These are explicit evaluation boundaries; changing an array does not change the source shape. A mesh approximates geometry rather than retaining exact BREP. For [STL/3MF](expimp.html), export directly without manually creating a mesh.
## Displaying a mesh

```python
import zencad as z

model = z.torus(30, 8) - z.box(60, 12, 12, center=True)
mesh = model.to_mesh(linear_deflection=0.35)
z.display(mesh, color=z.orange, display_mode="shaded_with_edges")
z.show()
```

The viewer displays the mesh directly without converting each triangle into a
BREP face. Display modes are `shaded_with_edges`, `shaded` and `wireframe`.
`linear_deflection` and `angular_deflection` control detail; `crease_angle`
defines edges where normals remain split.

## Polyhedron

`polyhedron(pnts, faces, shell=False)` builds a shape from vertices and faces
specified by vertex indices. Set `shell=True` to construct a shell instead of a solid.

```python
import zencad as z

mesh = z.sphere(10).to_mesh(0.5)
model = z.polyhedron(mesh.positions, mesh.triangles)
z.display(model)
z.show()
```

![Polyhedron from a sphere triangulation](../images/generic/polyhedron0.png)

## Convex hull

`convex_hull` computes face indices for the convex hull of a point set;
`convex_hull_shape` constructs the corresponding shape. SciPy is required.
`incremental` and `qhull_options` are passed to the SciPy algorithm;
`convex_hull_shape(..., shell=True)` creates a shell instead of a solid.

```python
import zencad as z

points = z.points([(0, 0, 0), (10, 0, 0), (10, 10, 0), (0, 10, 0), (5, 5, 10)])
model = z.convex_hull_shape(points)
z.display(model)
z.show()
```

![Convex hull of five points](../images/generic/convex_hull0.png)
::
