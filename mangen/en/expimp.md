# Export Import

Export/import operations differ from most operations of the zencad library in that they operate not only on objects in program memory, but also on files.

---
## STL
Create an STL mesh file located in the path from the solid model model.
The `delta` parameter determines the granularity. The smaller the delta, the smaller the size of the polygons.
```python3
to_stl(model, path, delta)
```

Importing SMALL stl and other mesh mesh formats is possible using third-party libraries such as trimesh. (see examples / Integration / trimesh)

---
Create a brep file of the BREP format located in the path `path` from the solid model` model`.
```python3
to_brep(model, path)
```

Read the brep file of the BREP format located in the path `path`. Return the resulting model.
```python3
m = from_brep(path)
```

---
## SVG
("0.34.0: Currently limited support. Not all curve types are supported.")

Create / read svg file from flat body `model`, located on path` path`.

```python3
to_svg(model, path)
model = from_svg(path)
```

Create / read svg string of flat body representation `model`.

```python3
svg = to_svg_string(model)
model = from_svg_string(svg)
```



## STL, STEP and 3MF export

Export is an explicit evaluation boundary: the shape is materialized, validated and written. Qt and `show()` are not required.

```python
import io
import zencad as z

part = z.box(20) - z.cylinder(4, 20).translate(10, 10, 0)
z.export_stl(part, "part.stl", binary=True)
z.export_step(part, "part.step", unit="mm")
z.export_3mf(part, "part.3mf", unit="mm", name="Bracket")
stream = io.BytesIO()
z.export_step(part, stream)
assert stream.getvalue().startswith(b"ISO-10303-21")
```

| Format | Stored data |
| --- | --- |
| STL | Triangle mesh; no unit metadata, so coordinates are scaled |
| STEP | Exact BREP geometry and units; ISO-10303-21 text |
| 3MF | Mesh, units and metadata; binary ZIP container |
| BREP | Native OCCT geometry through `to_brep`/`from_brep` |

STL/STEP/3MF accept a path or binary stream with `write(bytes)`. Units include `mm`, `cm`, `m`, `um`, `in`, `ft` and their full names. Internal geometry uses millimetres. `linear_tolerance` and `angular_tolerance` control STL/3MF meshing; STEP requires no tessellation. Linear tolerance uses export units.

Invalid shapes raise `ShapeValidationError`; write failures raise `OSError` with format and destination context. `to_stl(shape, path, delta)` remains an ASCII compatibility facade returning `True` on success.

```python
import zencad as z

z.to_brep(z.box(3), "part.brep")
restored = z.from_brep("part.brep")
restored.assert_valid()
```

SVG uses `to_svg`/`to_svg_string` and `from_svg`/`from_svg_string`. STEP/3MF export does not imply matching import support. [Full export contract](../development/export-formats.md).
