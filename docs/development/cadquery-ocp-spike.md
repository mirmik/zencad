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

That boundary is implemented in `zencad/occ_compat.py`. Subsequent ports must:

- import ordinary OCCT classes directly from `OCP`;
- use `occ_compat` for the renamed static calls, downcasts, BREP I/O, precision,
  sewing, backend version, and typed standard exceptions;
- add a focused wrapper only when a real pythonocc/OCP incompatibility is found;
- never add module-level monkey patches or an `OCC.Core` compatibility tree.

The adapter deliberately imports only OCP. If the package is absent, lacks
version metadata, or lacks one of the APIs required by the adapter, importing
it raises an actionable error recommending `cadquery-ocp-novtk`; it does not
start the GUI or invoke an installer.

## Geometry migration finding

Unlike pythonocc, OCP's `TopoDS_Shape` objects are not directly pickleable.
ZenCad's evalcache therefore cannot persist a `Shape` by storing its wrapped
OCCT object. `Shape.__getstate__` and `Shape.__setstate__` now normalize this
through an in-memory BREP stream. This keeps the public Python object
pickleable and also avoids depending on private binding internals.

The migrated geometry/topology set passes 56 existing headless tests plus the
primitive, transform, boolean, mass, bounds, and topology portions of the
migration baseline on OCP 7.9.3.1. Text construction and file conversion are
excluded here because they are tracked by the separate text and I/O migration
tasks.

The production migration must retain a separate GUI extra, but it does not
need the VTK-enabled OCP distribution unless later viewer work demonstrates a
real use of the OCP VTK bridge.
