# Typed API parity contract

This document defines the compatibility gate between the legacy ZenCad
geometry API and the private typed domain layer. The machine-readable source
of truth is [`typed-api-parity.json`](typed-api-parity.json); it is checked by
`tools/check_typed_api_parity.py` and `utest/typed_api_parity_test.py`.

## Compatibility promise

The public cutover does not reduce ZenCad's intentionally supported geometry
surface. Existing factories, operations, domain methods, transformations, and
mesh/conversion/display boundaries must have a truthful typed equivalent before
`zencad` starts returning typed handles by default.

Compatibility means preserving the operation and its useful parameter and
result semantics. It does not mean preserving `evalcache.LazyObject`, policy-
dependent result classes, mutable OCP ownership, historical tuple expansion,
or names that leaked accidentally through `import *`. Known broken behavior is
classified as `repair` and receives an explicit replacement contract rather
than being copied silently.

The contract covers definitions from the following user-facing families:

- scalar/point/vector/quaternion values and their algebra;
- similarity and affine transformations;
- `Shape`, topology queries, curve queries, bounds, and inherited transform
  helpers;
- solid, face, wire, shell, Curve, Curve2, Surface, and builder factories;
- sweeps, booleans, fillet/chamfer, offset, sewing, unification, projection,
  and nearest-topology queries;
- mesh, BREP/STL/SVG conversion, and display materialization boundaries.

Low-level OCP compatibility helpers, lazy proxy implementation classes, GUI
widgets, cache settings, colors, and unrelated utilities remain supported by
their existing modules but are outside the typed-domain replacement surface.

## Status model

- `implemented`: the private typed layer already provides the complete domain
  capability.
- `partial`: the typed core exists, but a legacy parameter variant, alias, or
  structured result remains.
- `missing`: no complete typed equivalent exists.
- `repair`: the legacy contract is broken or conflicts with the accepted
  immutable typed model and needs a deliberate repaired spelling.
- `unchanged`: the entry remains outside the lazy/domain migration.

The expanded inventory contains 385 types, functions, methods, and
operators:

| Family | Total | Implemented | Partial | Missing | Repair | Unchanged |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Values | 44 | 42 | 0 | 0 | 2 | 0 |
| Transforms | 64 | 64 | 0 | 0 | 0 | 0 |
| Topology and bounds | 117 | 112 | 0 | 0 | 4 | 1 |
| Constructors | 92 | 92 | 0 | 0 | 0 | 0 |
| Sweeps and operations | 50 | 50 | 0 | 0 | 0 | 0 |
| Mesh, convert, display | 18 | 16 | 0 | 0 | 0 | 2 |
| **Total** | **385** | **376** | **0** | **0** | **6** | **3** |

These counts describe API surface, not comparable implementation effort. Many
rows are aliases, so a single typed operation can close several of them.
Conversely, a sweep or affine-transform row can require a substantial domain
design.

#2039 closes the value and similarity-transform families. The legacy
`point3`, `vector3`, and `quat` spellings, bulk value constructors, similarity
aliases, `MultiTransform`, transform arrays, and inherited `Shape` methods now
keep their graphs behind stable typed handles. The two value repairs are the
split of ambiguous `xyz` into `Point3`/`Vector3` and rejection of historical
point division. The affine repair #2024 now provides an immutable
`AffineTransform` domain handle, deterministic matrix serialization, general
composition, and explicit `gp_GTrsf` materialization. `GeneralTransformation`
remains a compatibility alias in the typed surface.

The first #2043 tranche adds graph-preserving sequence and variadic boolean
operations alongside the pairwise operators. `section` now accepts typed shape
operands and the legacy scalar/vector plane forms, while every result remains
an explicit general `Shape` because boolean topology is not subtype-stable.
The compatibility tranche exposes root-style fillet/chamfer entry points,
dynamic topology restoration, and `triangulate` aliases without weakening the
stable handle contracts. Mesh node and triangle access now returns immutable,
zero-based rows for either `MeshData` or an explicit native triangulation.
Offset, thick-solid construction, solid repair, sewing, and same-domain
unification now remain inside typed expression graphs. Sewing overloads expose
the knowable result family (`Wire` or `Shell`), while thick-solid and repair
operations retain `Solid` and unification retains the input handle subtype.
Nearest-topology queries now return the exact requested topology handle and
fail explicitly when that topology is absent. Curve projection returns a
`CurveProjection` record containing graph-preserving point, parameter, and
distance handles. With this tranche, every non-sweep operation owned by #2043
is implemented; the remaining rows in this family belong to the sweep tasks.

#1993 adds deterministic solid partitioning to the same boolean backend.
`split()` returns a deferred `SplitResult`, while `slice()` returns an ordered
`SliceResult` whose `lower` and `upper` solids follow the plane normal. Both
legacy lazy nodes and typed handles share non-dividing and ambiguous-result
errors, coordinate-axis planes, arbitrary planar faces, and `(origin, normal)`
plane descriptions.

#1994 adds face draft as another graph-preserving modeling operation. Legacy
lazy shapes and typed `Solid` handles share the OCCT draft-angle backend,
selected Face operands, pull direction, angle-sign convention, and planar
neutral descriptions. Positive angles remove material along the pull direction;
negative angles add it, while the neutral plane remains fixed.

#2036 and #2042 complete the sweep family. Sweep laws are frozen compositions
of typed curves, scalars, intervals, and enums; only the terminal Surface
operation materializes mutable OCCT laws. Topology extrusion, revolution,
loft, pipe, pipe-shell, and rolled `revol2` operations preserve graph inputs
and return stable `Shape`, `Shell`, or `Solid` handles. `PipeTrihedron` and
`PipeTransition` replace string/integer option tables, and the single-profile
`sweep` spelling is a characterized compatibility alias.

The first #2044 tranche makes BREP file round-trips and native mesh conversion
explicit typed boundaries. `Runtime.from_brep()` snapshots imported topology
into a stable `Shape`; `Runtime.to_brep()` materializes only for the write.
`MeshData.mesh_to_poly_triangulation()` and its Runtime adapter return fresh
native triangulations without exposing mutable mesh state.
STL and SVG file/string adapters now share the same explicit boundary model.
Exports operate on isolated native snapshots, while SVG imports snapshot the
legacy parser result into the receiving Runtime. Paths, meshing controls, and
mapping policy are validated before file or native work begins.
Managed and direct display scenes now accept typed `Shape`, `MeshData`, and
`Point3` handles. Managed drafts retain the handles until snapshot encoding;
direct scenes convert them only while constructing the interactive renderer
object. No typed geometry module imports Qt, and the existing display aliases
and highlighting functions preserve their compatibility behavior.

#2040 closes topology predicates, CurveAlgo queries, modeling convenience
methods, native adaptor boundaries, structured shape properties, and immutable
BoundaryBox compatibility. Its four BoundaryBox repairs replace mutation with
constructors or returned values. The former non-uniform `scaleX/Y/Z/XYZ`
repairs now route through the typed affine boundary and preserve the concrete
topology handle.

The first #2041 constructor tranche completes all legacy solid factories:
`cube`, `sphere`, `cylinder`, `cone`, `torus`, `halfspace`, and `make_solid`.
Angular, centering, and graph-scalar variants retain exact `Solid` handles.
`nullshape` is represented as an ordinary empty `Shape`, the algebraic zero of
topology, with `empty_shape` as its explicit spelling; it is neither optional
nor a separate domain type.

The second #2041 tranche separates geometric Curve factories from root-compatible
topological constructors: `interpolate_curve`, `bezier_curve`, and
`bspline_curve` return Curve, while `interpolate`, `bezier`, and `bspline`
return Edge. `circle_arc`, `make_edge`, `make_wire`, `rounded_polysegment`, and
`helix` complete the legacy wire factory set. Curve-to-Edge conversion and
Curve transforms remain graph operations; only the explicit native adaptor
methods materialize OCP objects.

The third #2041 tranche completes the legacy `wire_builder` surface as typed
`WireBuilder`. The builder is a deliberately mutable authoring cursor, but its
edge list, current point, tangents, curve parameters, and final wire are stable
typed graph handles. Fluent editing therefore emits no deferred evaluation;
`build()` and `doit()` return `Wire` without themselves materializing it. SVG
endpoint arcs choose their center inside one resolved, cacheable operation,
while ordinary circular, elliptical, interpolation, relative, and closing
operations compose the existing typed primitives. Descending curve intervals
are represented as correctly oriented edges instead of OCCT's periodic
complement.

The fourth #2041 tranche restores the planar constructor surface. Geometric
curve factories now use the unambiguous `circle_curve` and `ellipse_curve`
spellings, while root-compatible `circle` and `ellipse` return `Face` or
`Edge` according to `wire`. Polygon, rectangle, square, and ngon variants
return exact `Face`/`Wire` handles; fill supports outer boundaries and holes.
`interpolate2`, `ruled`, `fix_face`, and `infplane` complete the non-text,
non-sweep Face constructors. The historically inverted partial-ellipse
`wire` branch is repaired consistently: `wire=True` means an edge boundary,
and `wire=False` means a filled sector.

The fifth #2041 tranche completes shell, polyhedron, convex-hull, and Platonic
factories. Sewing one or more `Face` handles now always produces an exact
`Shell`; filling accepts only that shell type and returns `Solid`. Polyhedron,
convex-hull shape, and all five Platonic factories preserve graph points and
scalars while selecting exact `Shell`/`Solid` handles through literal flag
overloads. The numeric `convex_hull` triangulation is the deliberate exception:
it returns immutable integer-index tuples and explicitly materializes its input
points at the SciPy/Qhull boundary.

The sixth #2041 tranche closes the remaining pure curve/surface methods.
`Curve2.rotate(ScalarInput)` is a serializable graph operation and keeps its
exact `Curve2` handle. `Surface.map(Curve2)` follows the truthful legacy native
result rather than the earlier provisional parity label: mapping a p-curve onto
a surface produces an `Edge`, with 3D curves built at resolved evaluation time.
Both operations remain deferred and cacheable.

The seventh #2041 tranche isolates OCCT text state from typed topology. The
domain-level `FontAspect` enum replaces public native font enums, while
`Runtime.register_font()` is deliberately immediate because OCCT registration
mutates a process-wide manager. `text_to_brep()` and its `textshape()` legacy
spelling return the exact `Compound` produced by the BREP text builder and keep
graph scalar sizes deferred. Text expressions deliberately bypass cache
read/write because the registered font table is external state absent from an
expression key.

The eighth #2041 tranche completes the constructor family with `widewire`.
Its spine and radius remain graph operands and the resolved adapter performs
the legacy planar pipe, joint, end-cap, boolean, and unification sequence
without creating a nested legacy lazy graph. The truthful result is `Shape`,
because OCCT returns a `Face` for a simple uncapped edge but a `Compound`
containing the result for capped or multi-edge spines. Evaluation and cache
policies do not change that public handle class.

The executable decomposition is:

- #2039 — values and similarity-transform compatibility;
- #2040 — topology, curve-query, and BoundaryBox methods;
- #2041 — all remaining geometry constructors and builders;
- #2036 + #2042 — extensible sweep-law contract and sweep implementations;
- #2043 — modeling operations and geometry queries;
- #2044 — mesh, conversion, and display adapters;
- #2024 — repaired affine/GeneralTransformation contract.

All implementation cards block the final public cutover #2013. Work may
proceed on every unblocked family while the legacy root remains unchanged.

## Machine check

Run:

```bash
python tools/check_typed_api_parity.py
python tools/check_typed_api_parity.py --render
```

The checker expands public source definitions and class methods, applies the
family defaults and per-symbol overrides from the JSON matrix, verifies that
every expanded entry has a typed contract and characterization suite, and
compares all legacy signatures with the committed SHA-256 snapshot. Adding,
removing, or changing a covered legacy definition therefore fails the gate
until the matrix is reviewed.

`--render` prints the complete per-symbol table with the canonical legacy
definition, current signature, status, typed target, and materialization rule.
The expanded table is intentionally generated instead of duplicated in this
document.

## Completion rule

Family migration cards may change `missing`, `partial`, and `repair` rows to
`implemented` only together with runtime characterization and static type
coverage. The final public cutover remains blocked until:

1. every typed-domain row is `implemented`, has an explicitly characterized
   `repair` contract, or is intentionally `unchanged`;
2. the signature snapshot and public root snapshot are reviewed;
3. the evalcache release and release-vehicle gates are complete;
4. installed-wheel, example, headless/display, and type-check gates pass.
