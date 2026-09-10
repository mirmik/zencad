# Export and import

Export evaluates geometry and writes a file; neither `show()` nor the graphical interface is needed.

| Format | Stored data | Write | Read |
| --- | --- | --- | --- |
| STL | Triangle mesh without units | `export_stl` | Through third-party libraries such as trimesh |
| STEP | Exact BREP geometry and units | `export_step` | No |
| 3MF | Mesh, units and metadata | `export_3mf` | No |
| BREP | OpenCascade geometry | `to_brep` | `from_brep` |
| SVG | Planar geometry, limited support | `to_svg` | `from_svg` |

## STL, STEP and 3MF

```python
import zencad as z

part = z.box(20) - z.cylinder(4, 20).translate(10, 10, 0)
z.export_stl(part, "part.stl", binary=True)
z.export_step(part, "part.step", unit="mm")
z.export_3mf(part, "part.3mf", unit="mm", name="Bracket")
```

Exporters interpret source coordinates as millimetres. `unit` selects the file units: `mm`, `cm`, `m`, `um`, `in`, `ft` or their full names. For example, with `unit="cm"`, a dimension of 20 is written as 2 centimetres. STL stores no unit metadata: only the coordinate scale changes.

`linear_tolerance` and `angular_tolerance` control STL/3MF mesh detail. Linear tolerance uses the file units; a smaller tolerance produces a finer mesh. STEP does not require triangulation.

A binary stream can be passed instead of a path:

```python
import io
import zencad as z

stream = io.BytesIO()
z.export_step(z.box(10), stream)
assert stream.getvalue().startswith(b"ISO-10303-21")
```

Invalid shapes raise `ShapeValidationError`; write failures raise `OSError`. `to_stl(model, path, delta)` is a shorthand for ASCII STL export; `delta` controls mesh detail, and success returns `True`.

## BREP

```python
import zencad as z

z.to_brep(z.box(3), "part.brep")
restored = z.from_brep("part.brep")
restored.assert_valid()
```

## SVG

For files, use `to_svg(model, path)` and `from_svg(path)`. For strings, use `to_svg_string(model)` and `from_svg_string(svg)`.

```python
import zencad as z

svg = z.to_svg_string(z.rectangle(20, 10))
restored = z.from_svg_string(svg)
restored.assert_valid()
```

SVG works with planar geometry; not all curve types are supported. An example of importing a low-polygon STL through trimesh is in `zencad/examples/Integration/trimesh`. [Export details](../development/export-formats.md).
