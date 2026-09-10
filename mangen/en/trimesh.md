# Triangulation and mesh

Functions for working with polygonal representation.

---
## Displayable mesh

`Shape.to_mesh()` builds an indexed `MeshData` triangle mesh. The mesh can be
passed directly to `disp`; the viewer renders it through `AIS_Triangulation`
without converting every triangle into a B-Rep face.

```python
model = torus(30, 8) - box(60, 12, 12, center=True)
mesh = model.to_mesh(linear_deflection=0.35)

controller = disp(mesh, color=color.orange)
show()
```

The default is `shaded_with_edges`: a shaded surface with all triangle edges.
The display mode can be selected when displaying the mesh:

```python
disp(mesh, display_mode="shaded_with_edges")  # поверхность и рёбра
disp(mesh, display_mode="shaded")             # только поверхность
disp(mesh, display_mode="wireframe")          # только рёбра
```

The mode of an already displayed object can be changed with
`controller.set_mesh_display_mode(...)`.

`MeshData` contains `positions`, `normals`, `triangles`, and
`triangle_face_ids`. `linear_deflection` and `angular_deflection` control
detail, while `crease_angle` determines where normals remain split across
sharp edges.

---
## Triangulation
Materializing a polygonal mesh provides arrays in the format (_nodes_, _triangles_), where _pnts_ is an array of points, and _triangles_ is an array of 3-tuples, indices of points.
The _deflection_ parameter is responsible for resolving the splitting.

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

-----------------------------
## Polyhedrone
A solid consisting of flat faces, specified by vertex points _pnts_ and an array of tuples of indices of points defining the faces.

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
## Convex hull
Construction of the convex hull of a set of points.
The scipy.spatial.ConvexHull procedure is used

_convex_hull_ computes an array of convex hull polygon point indices.
_convex_hull_shape_ builds a convex hull using the _polyhedron_ procedure.

Options:
_incremental_ and _qhull_options_ are scipy.spatial.ConvexHull options (see scipy documentation).
_shell_ - create a shell instead of a body.

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


## Domain values and evaluation

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
