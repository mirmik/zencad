# Shape validation and repair

ZenCad exposes OCCT topology diagnostics as a versioned, JSON-ready
`ValidationReport`. Validation is read-only and is an explicit materialization
boundary in both the legacy and typed APIs:

```python
report = shape.validate(exact=False, parallel=False)
if not report.valid:
    print(report.to_dict())

shape.is_valid()
shape.assert_valid()  # returns the same shape or raises ShapeValidationError
```

Each `ValidationIssue` has a stable snake-case `code`, the original
`occt_status`, the failing `path` and `shape_type`, and optional context fields.
Paths follow the direct topology hierarchy, for example
`solid/shell[0]/face[2]/wire[0]`. OCCT sometimes reports a failure only in a
parent context; an open shell used as a solid therefore reports `not_closed`
on `solid/shell[0]` with `context_path="solid"`.

`BRepCheck_Analyzer` considers a standalone open shell valid topology. Use
`shape.is_closed()` when the application requires closure independently of
topological consistency.

## Explicit shape-changing operations

Diagnostics, redundant-boundary cleanup, general healing, and sewing are
separate operations:

```python
cleaned = shape.clean()
healed = shape.heal(tolerance=1e-7, max_tolerance=1e-3)
shell = zencad.sew(faces)
```

- `clean()` removes same-domain redundant edges and faces.
- `heal()` runs general OCCT `ShapeFix` with bounded tolerances. It is
  best-effort; validate the result when validity is required.
- `sew()` joins supplied edges/wires or faces/shells and remains an independent
  modeling operation.

`clean()` and `heal()` operate on owned copies and never modify their source.
They retain laziness and, in the typed API, preserve the concrete topology
handle (`Solid`, `Face`, and so on). Validation never performs hidden repair.

Reports can be passed directly to inspection or logging code:

```python
import json

payload = json.dumps(shape.validate().to_dict(), sort_keys=True)
```
