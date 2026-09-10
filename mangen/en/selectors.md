# Topology and selectors

Geometric objects consist of simpler components: solids, faces, edges and vertices. See the [BREP introduction](geomcore.html).

## Getting components

These methods return `ShapeList` collections with the corresponding element types:

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

Use `vertex.point()` to get vertex coordinates. Indexing, slicing, filtering and sorting preserve the computation graph; `len()`, iteration, `geometry_types()` and `group_by()` evaluate the collection.

## Selecting elements

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

An index does not identify a particular face: the order can change after editing the model. Prefer selection by geometric properties.

`fillet` and `chamfer` accept edges; `draft` accepts faces. Details: [selector contract](../development/topology-selectors.md).

## Nearest element

These functions return the component of `shp` nearest to `pnt`:

```python
near_edge(shp, pnt) # -> Edge
near_face(shp, pnt) # -> Face
near_vertex(shp, pnt) # -> Vertex; .point() -> Point3
```

## Checking contents and restoring types

Check for the absence of solids (faces and edges may still be present):

```python
len(shp.solids()) == 0
```

`restore_shapetype` extracts a single suitable component. To require exactly one solid, use `shp.solids().only()`.

```python
original_shp = restore_shapetype(shp)
```
