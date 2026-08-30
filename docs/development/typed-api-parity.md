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

The expanded inventory contains 380 types, functions, methods, and
operators:

| Family | Total | Implemented | Partial | Missing | Repair | Unchanged |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Values | 44 | 42 | 0 | 0 | 2 | 0 |
| Transforms | 64 | 55 | 0 | 0 | 9 | 0 |
| Topology and bounds | 117 | 108 | 0 | 0 | 8 | 1 |
| Constructors | 92 | 92 | 0 | 0 | 0 | 0 |
| Sweeps and operations | 45 | 3 | 4 | 38 | 0 | 0 |
| Mesh, convert, display | 18 | 2 | 3 | 11 | 0 | 2 |
| **Total** | **380** | **302** | **7** | **49** | **19** | **3** |

These counts describe API surface, not comparable implementation effort. Many
missing entries are aliases; a single typed operation can close several rows.
Conversely, a sweep or affine-transform row can require a substantial domain
design.

#2039 closes the value and similarity-transform families. The legacy
`point3`, `vector3`, and `quat` spellings, bulk value constructors, similarity
aliases, `MultiTransform`, transform arrays, and inherited `Shape` methods now
keep their graphs behind stable typed handles. The two value repairs are the
split of ambiguous `xyz` into `Point3`/`Vector3` and rejection of historical
point division. The nine remaining transform repairs are exclusively the
non-uniform affine contract owned by #2024.

#2040 closes topology predicates, CurveAlgo queries, modeling convenience
methods, native adaptor boundaries, structured shape properties, and immutable
BoundaryBox compatibility. Its four BoundaryBox repairs replace mutation with
constructors or returned values. The other four repairs in this family are
the non-uniform `scaleX/Y/Z/XYZ` methods owned by affine card #2024.

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

1. every typed-domain row is `implemented` or explicitly `unchanged`;
2. the signature snapshot and public root snapshot are reviewed;
3. the evalcache release and release-vehicle gates are complete;
4. installed-wheel, example, headless/display, and type-check gates pass.
