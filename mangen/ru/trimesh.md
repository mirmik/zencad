# Триангуляция и меш

Функции для работы с полигональным представлением.

---
## Отображаемый меш

Метод `Shape.to_mesh()` строит индексированную треугольную сетку `MeshData`.
Такую сетку можно передать непосредственно в `disp`: просмотрщик отображает
её непосредственно, без преобразования треугольников в BREP-грани.

```python
model = torus(30, 8) - box(60, 12, 12, center=True)
mesh = model.to_mesh(linear_deflection=0.35)

controller = disp(mesh, color=color.orange)
show()
```

По умолчанию используется режим `shaded_with_edges`: затенённая поверхность
с рёбрами всех треугольников. Режим можно выбрать при отображении:

```python
disp(mesh, display_mode="shaded_with_edges")  # поверхность и рёбра
disp(mesh, display_mode="shaded")             # только поверхность
disp(mesh, display_mode="wireframe")          # только рёбра
```

Режим уже отображённого объекта можно изменить через
`controller.set_mesh_display_mode(...)`.


---
## Данные сетки

`Shape.to_mesh(linear_deflection, angular_deflection=...)` возвращает `MeshData`. Меньшее отклонение даёт более подробную сетку; `crease_angle` задаёт угол, начиная с которого нормали соседних треугольников разделяются для сохранения резких рёбер.

`positions` — координаты вершин, `normals` — нормали, `triangles` — тройки индексов вершин, `triangle_face_ids` — соответствие треугольников граням исходной формы.

Сигнатура:
```python
mesh = shp.to_mesh(deflection)
nodes, triangles = mesh.positions, mesh.triangles
```

Пример:
```python
m=sphere(10)
mesh = m.to_mesh(0.1)
nodes, triangles = mesh.positions, mesh.triangles

print("count_of_nodes:", len(nodes))
print("count_of_triangles:", len(triangles))

print("first_five_nodes:", nodes[:5])
print("first_five_triangles:", triangles[:5])

```

### NumPy и OCP

Сетка вычисляется при запросе её данных. `.value()` возвращает численные данные и счётчики, `.to_numpy()` — массивы NumPy, `.native()` — `Poly_Triangulation` для работы с OCP.

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

Изменение полученных массивов не меняет исходную форму. Сетка — приближение геометрии. Для [STL/3MF](expimp.html) можно вызвать экспорт без ручного построения сетки.

-----------------------------
## Полигедрон
Объёмное тело, состоящее из плоских граней, заданное точками вершин _pnts_ и массивом кортежей индексов точек, задающих грани.

Сигнатура:
```python
polyhedron(pnts, faces, shell=False)
```

Пример:
```python
m=sphere(10)
mesh = m.to_mesh(0.1)
nodes, triangles = mesh.positions, mesh.triangles
disp(polyhedron(nodes, triangles))
```
![](../images/generic/polyhedron0.png)

----------------------------------------------
## Выпуклая оболочка
Построение выпуклой оболочки множества точек.
Используется процедура scipy.spatial.ConvexHull

_convex_hull_ вычисляет массив индексов точек полигонов выпуклой оболочки.
_convex_hull_shape_ строит выпуклую оболочку, используя процедуру _polyhedron_.

Опции:
_incremental_ и _qhull_options_ являются опциями scipy.spatial.ConvexHull (см. документацию scipy).
_shell_ - создать оболочку вместо тела.

Сигнатура:
```python
convex_hull(pnts, incremental=False, qhull_options=None)
convex_hull_shape(pnts, shell=False, incremental=False, qhull_options=None)
```

Пример:
```python
pnts = points([
	( 0,  0,  0),
	(10,  0,  0),
	(10, 10,  0),
	( 0, 10,  0),
	( 5,  5, 10),
])

print(convex_hull(pnts))
disp(convex_hull_shape(pnts))
```

![](../images/generic/convex_hull0.png)
