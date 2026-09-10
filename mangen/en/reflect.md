# Reflection
Complex geometric objects are composed of simpler ones. This group of functions and methods allows you to decompose complex objects into their constituent components.

To work with these functions, it is recommended to study the topological structure of models in the _OpenCascade_ kernel. (You can get started with the section [Introduction to BREP Representation of Geometric Models](geomcore.html)) 

---------------------------
## Checking contents
For a solid operation, test `len(shape.solids()) == 0` to check that no solid components remain. This is not a general emptiness test: a nonempty face or curve contains no solids either.

Сигнатура:
```python
len(shp.solids()) == 0
```
Пример:
```python
a = box(10, center=True)
b = sphere(r=10)
len((a - b).solids()) == 0 # True
```

---------------------------
## Arrays of base objects
This family of methods allows you to retrieve and filter the underlying objects you need.

Methods return a `ShapeList` with the corresponding element type. Use collection methods such as `filter_by`, `filter_by_position` and `planar` for [selection](selectors.html). A vertex is a `Vertex`; obtain its coordinates with `.point()`.
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

---------------------------------------------------
## Taking a base object using the closest point method
Sometimes you want to extract a specific base object from a complex object.
In this case, you can use the base point method.

The following functions implement the closest point method and return the closest base object of the corresponding type to _pnt_ belonging to the complex _shp_ object. 

```python
near_edge(shp, pnt) # -> Edge
near_face(shp, pnt) # -> Face
near_vertex(shp, pnt) # -> Vertex; .point() -> Point3
```

---
## Type restoration
Types such as `Solid`, `Face` and `Edge` are directly available. `restore_shapetype` examines a shape and extracts a single suitable component. To require exactly one solid, use `shp.solids().only()`.

```python
original_shp = restore_shapetype(shp)
```
