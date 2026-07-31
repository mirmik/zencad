# cadquery-ocp compatibility spike

This note records the initial compatibility check for migrating ZenCad from
`pythonocc-core` to the PyPI-distributed `cadquery-ocp` bindings. Conda is not
part of the target installation path.

## Result

The spike passed with `cadquery-ocp-novtk==7.9.3.1.1` on CPython 3.10 and
Linux x86-64. It covers:

- box and sphere construction;
- transformation and boolean fuse;
- `TopExp_Explorer` traversal and `TopoDS` downcast;
- volume properties through a static `_s` method;
- `BinTools` BREP write/read round-trip;
- propagation of a typed `Standard_DomainError` exception;
- imports of the `AIS`, `Aspect`, `Graphic3d`, and `V3d` modules used by the
  ZenCad viewer.

Reproduce it without conda:

```bash
python3 -m venv /tmp/zencad-ocp-spike
/tmp/zencad-ocp-spike/bin/python -m pip install \
  cadquery-ocp-novtk==7.9.3.1.1
/tmp/zencad-ocp-spike/bin/python expers/ocp_compatibility_spike.py
```

The `novtk` distribution installs only itself and the small
`cadquery-ocp-proxy` package. The full `cadquery-ocp` distribution also pulls
VTK, Matplotlib, NumPy, and their dependencies. ZenCad does not currently use
the OCP VTK bridge, so `cadquery-ocp-novtk` is the preferred base dependency.

## Import compatibility

The ZenCad source currently references 168 symbols from 47 `OCC.Core`
modules. With OCP 7.9.3.1, 157 symbols are available under the same module and
symbol names after replacing `OCC.Core` with `OCP`.

The non-mechanical replacements found by the spike are:

| pythonocc API | OCP API |
| --- | --- |
| `brepbndlib.Add` | `BRepBndLib.Add_s` |
| `brepfill.Face` | `BRepFill.Face_s` |
| `brepgprop.SurfaceProperties` | `BRepGProp.SurfaceProperties_s` |
| `brepgprop.VolumeProperties` | `BRepGProp.VolumeProperties_s` |
| `breplib.BuildCurves3d` | `BRepLib.BuildCurves3d_s` |
| `breptools.Read` / `Write` | `BRepTools.Read_s` / `Write_s` |
| `precision_Confusion()` | `Precision.Confusion_s()` |
| `topexp.*` | static methods on `TopExp`, with `_s` |
| `topods.Face`, etc. | `TopoDS.Face`, etc. |
| `gp_DZ()` | `gp.DZ_s()` |
| `BRepOffsetAPI_Sewing` | `BRepBuilderAPI_Sewing` |

The imported `bintools` alias is absent in OCP and appears unused in ZenCad.
`BinTools_ShapeSet` itself is present.

`OCC.Core.Addons` is the only referenced module absent from OCP. Its font
registration and `text_to_brep` helpers require a dedicated replacement using
the standard OCCT font APIs; that work is tracked separately.

## Integration direction

Use direct `OCP.<module>` imports for the 157 matching symbols. Introduce a
small internal compatibility module only for the recurring renamed static
helpers and downcasts listed above. Do not emulate the complete `OCC.Core`
package hierarchy: a broad facade would preserve obsolete pythonocc concepts
and make future OCP upgrades harder to audit.

The production migration must retain a separate GUI extra, but it does not
need the VTK-enabled OCP distribution unless later viewer work demonstrates a
real use of the OCP VTK bridge.
