# Typed topology selectors

The public geometry API exposes every topology query as a composable
`ShapeList[T]`. `DeferredSequence` remains an alias for compatibility, while
new annotations should use the more descriptive name:

```python
import zencad as cad

with cad.using_context(cad.Context.deferred(cache=False)):
    body = cad.box(10, 20, 30)
    vertical = body.edges().filter_by(cad.Axis.Z)
    top = body.faces().planar().sort_by(cad.Axis.Z)[-1]
```

Filtering and sorting compose new expression nodes. Indexing and slicing also
remain in the graph. `len()`, iteration, `geometry_types()`, and `group_by()`
are explicit materialization boundaries because their Python result shape must
be known to the caller.

## Criteria and named selectors

- `filter_by(GeomType.PLANE)` selects a stable geometry category.
- `filter_by(Axis.Z)` selects line/circle directions and supported surface
  axes parallel to Z.
- `filter_by(Plane.xy(z))` selects shapes whose center lies on that plane.
- `filter_by_position(Axis.Z, z)` is the coordinate-oriented spelling.
- `normal_to(Axis.Z)` selects planar faces with parallel normals.
- `planar()` is shorthand for `filter_by(GeomType.PLANE)`.
- `longer_than(value)` compares the OCCT linear measure of edges or wires.
- `sort_by(Axis.Z)` orders by center projection, then lexicographic center.
- `sort_by_distance(point)` uses exact minimum OCCT shape-to-point distance,
  then lexicographic center. `reverse=True` reverses the complete ordering.
- `group_by(GeomType)` returns groups in first-occurrence order.
- `largest()` returns the maximum by linear, surface, or volume measure;
  equal measures select the lexicographically smallest center.
- `only()` requires exactly one result.

Direction tolerance is an angular tolerance in radians and defaults to
`1e-7`. Position tolerance uses model units and also defaults to `1e-7`.
Direction comparison ignores sign: geometry parallel to `+Z` or `-Z` belongs
to the same directional group. An empty `largest()` and any zero-or-many
`only()` fail with a diagnostic `ValueError` when the returned handle is
evaluated.

Topology queries (`vertices`, `edges`, `wires`, `faces`, `shells`, `solids`,
`compsolids`, and `compounds`) sort results lexicographically by center X, Y, Z.
Vertices use their coordinates; edges/wires use the linear center of mass,
faces/shells the surface center, and solids/compsolids the volume center.
Compounds use the highest dimensional geometry present; vertex-only compounds
use the bounding-box center and empty compounds use the origin.
Center keys round coordinates to nine decimal places in model units to suppress
small integration noise. The same key breaks ties in explicit selectors.

`vertices()` remains unique by OCCT `IsSame`; other queries retain explorer
occurrences, including repeated shared subshapes. Sorting changes their order,
not their multiplicity. Filters preserve the resulting order; grouping retains
the first-occurrence order of the current sequence.

This intentionally replaces traversal-dependent indexing. Query and sequence
operation versions are bumped so dependent cached indexed results cannot retain
the old ordering. No persistent topological identity across modeling edits is
promised. Shapes with equal rounded center keys retain their input order;
distinguishing these candidates is explicitly deferred. Distinct centers closer
than the rounding precision are subject to the same limitation. Reproducibility
across numerical changes that cross rounding boundaries is not guaranteed.

## Modeling operations

`ShapeList[Face]` is accepted directly by `draft`. `ShapeList[Edge]` is
accepted directly by `fillet` and `chamfer`; repeated occurrences of one OCCT
edge are deduplicated before the builder is called, and foreign edges produce
an explicit error.

```python
with cad.using_context(cad.Context.deferred(cache=False)):
    body = cad.box(10)
    vertical = body.edges().filter_by(cad.Axis.Z)
    rounded = cad.fillet(body, 1, vertical)
    tapered = cad.draft(body, body.faces().normal_to(cad.Axis.X), 0.05)
```
