# Headless STL, STEP, and 3MF export

The explicit export layer writes a `Shape` to a path or binary stream without
creating a Scene, importing Qt, or depending on the legacy lazy file creator:

```python
zencad.export_stl(shape, "part.stl", binary=True)
zencad.export_step(shape, "part.step", unit="mm")
zencad.export_3mf(
    shape,
    "part.3mf",
    unit="mm",
    name="Bracket",
    metadata={"Designer": "Example"},
)
```

The typed API provides the same module functions and
`Runtime.export_stl/step/3mf`. All are explicit materialization boundaries and
operate on owned shape snapshots. Invalid topology raises
`ShapeValidationError` before writing.

## Units and tessellation

`LengthUnit` accepts `micron`, `millimeter`, `centimeter`, `meter`, `inch`, and
`foot`; short aliases such as `um`, `mm`, `cm`, `m`, `in`, and `ft` are also
accepted. ZenCad's internal geometry is millimetres.

- STL has no unit metadata, so coordinates are scaled into the requested unit.
- STEP retains exact BREP geometry and declares the selected length unit in the
  exchange model. STEP is ISO-10303-21 text; `binary=True` is rejected.
- 3MF stores both scaled mesh coordinates and the unit attribute. It is always
  a ZIP-based binary container; `binary=False` is rejected.

`linear_tolerance` and `angular_tolerance` control tessellation for STL and
3MF. Both must be finite and positive, and linear tolerance uses the exported
unit. STEP exports exact geometry and therefore has no tessellation options.

## Destinations and compatibility

Destinations may be `str`, `PathLike`, or an object with `write(bytes)`. A
failed, short, read-only, or otherwise invalid destination raises `OSError`
that names the format and target. Backend transfer failures are not converted
to a context-free `False`.

`to_stl(shape, path, delta)` remains as the compatibility facade. It keeps its
ASCII output and successful `True` result, while failures now raise with
context. `to_brep` is unchanged; STEP is available through `export_step`.
