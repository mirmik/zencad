# Introduction to BREP geometry

ZenCad builds on the functionality and object structure of the OpenCascade geometry kernel, which uses BREP (boundary representation) for geometric models.

A basic understanding of BREP and the kernel's topological structure helps when using the library's more advanced features.

------------------------------------------------------
## Boundary representation

Boundary representation describes bodies through their boundaries.

An object is defined topologically, through references to its bounding objects, and geometrically, through the rule that defines its shape. Its bounding objects are described in the same way.

For example, a cube is a solid enclosed by a shell of six faces. Each face is defined geometrically by a plane and bounded by four edges. Each edge is defined by a straight line and bounded by two vertices.

Different BREP libraries may divide objects into classes differently, but the general idea stays the same. ZenCad uses the OpenCascade class system.

------------------------------------------------------
## Geometric object classes
| ZenCad | OpenCascade | Composite | Dimension | Description |
| --- | --- | --- | --- | --- |
| Shape | TopoDS_Shape | Unspecified | Unspecified | Abstract geometric object |
| Vertex | TopoDS_Vertex | No | 0 | Vertex |
| Edge | TopoDS_Edge | No | 1 | Edge |
| Wire | TopoDS_Wire | Yes | 1 | Composite curve |
| Face | TopoDS_Face | No | 2 | Face |
| Shell | TopoDS_Shell | Yes | 2 | Shell |
| Solid | TopoDS_Solid | No | 3 | Solid body |
| CompSolid | TopoDS_CompSolid | Yes | 3 | Set of solids |
| Compound | TopoDS_Compound | Yes | Unspecified | Composite object |

`Vertex` is a topological vertex; `Point3` holds coordinates. `shape.vertices()` returns a collection of vertices; `vertex.point()` obtains a point.

------------------------------------------------------
## More about the kernel
OpenCascade is extensive, with far more tools than this brief introduction can cover.

For details, refer to the kernel documentation:
[Technology Overview](https://www.opencascade.com/doc/occt-7.3.0/overview/html/index.html)<br>
[Reference Manual](https://www.opencascade.com/doc/occt-7.3.0/refman/html/index.html)
