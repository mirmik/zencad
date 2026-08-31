# Typed domain migration

> Status: private typed kernel complete; full public API parity is in progress.
> The characterization baseline, evalcache v2 substrate, value/transform
> algebra, Shape/topology, Curve/Curve2/Surface, BoundaryBox, MeshData, and
> connected integration gates are implemented. The legacy public API remains
> active while the complete parity contract is migrated; no public typed-domain
> cutover described here is implemented yet. The accepted
> direction and rationale are recorded in
> [Typed domain handles and an internal lazy graph](../architecture-council/2026-08-30-typed-domain-handles.md).

## Objective

Give ZenCad one stable public runtime type for every supported domain value.
Lazy evaluation and cache state remain inside these types and do not appear as
`evalcache.LazyObject` values in normal user code.

The migration is developed in `feature/migration`; the corresponding evalcache
work is developed in its `v2` branch. Public API replacement is delayed until
a complete internal vertical slice passes all gates.

## Development checkout

ZenCad and evalcache are developed as two adjacent repositories. The Python
environment used for migration work must load the `v2` checkout rather than a
previously published evalcache wheel:

```bash
python -m pip install -e ../evalcache
python -c 'import evalcache; print(evalcache.__file__)'
```

The printed path must reside under the local evalcache checkout. A local path
must not be added to ZenCad package metadata because it would make published
artifacts machine-specific.

## Dependency order

```text
characterization baseline
          |
          v
evalcache Expression/Evaluator and cache protocols
          |
          v
internal typed vertical slice
          |
          +--> Scalar/Point/Vector/Quaternion/Transform algebra
          +--> Shape/topology/typed sequences
          +--> Curve/Surface/Mesh and runtime boundaries
                         |
                         v
                 public API cutover
                         |
                         v
                  PEP 561 publication
                         |
                         v
                  legacy API removal
```

## Stage 1: characterization baseline

Status: complete. The executable baseline lives in
`utest/migration_baseline_test.py` and passes as part of the full ZenCad suite.

Record the current observable behaviour without preserving implementation
accidents such as cache hashes or proxy classes:

- representative geometric and numeric results;
- lazy/eager and cache-on/cache-off evaluation timing;
- cache reuse across fresh processes;
- exception types, operation context, and tracebacks;
- common `.unlazy()`, native accessor, and custom `@lazy` scenarios;
- example-model and installed-wheel behaviour;
- tree construction, cold evaluation, cache-hit, and memory benchmarks.

Exit gate: the baseline can distinguish a geometric regression from an
intentional type-model change.

### Compatibility inventory

The 2026-08-30 baseline is executable in
`utest/migration_baseline_test.py`. The observations below describe the old
runtime and are not promises of the target API.

| Area | Current observable behaviour | Migration treatment |
| --- | --- | --- |
| Evaluation policy | There is no separate typed eager evaluator; deferred mode returns proxies while `onplace` immediately exposes resolved values | Introduce explicit evaluator policy without changing public result classes |
| Shape factories | Deferred mode returns `LazyObjectShape`; `onplace` returns `Shape` | Intentional incompatible change: both policies return one `Shape` handle |
| Scalar queries | `mass()` and similar queries return generic `LazyObject` or built-in values depending on policy | Replace with stable `Scalar` handles; materialize only at documented boundaries |
| Topology collections | `faces()` is a generic `LazyObject`; indexing produces another generic `LazyObject`; `len()` materializes | Replace with typed deferred sequences and typed topology elements |
| Curve, Curve2, Surface | Deferred factories erase the result behind generic `LazyObject`; `onplace` exposes the resolved class | Introduce stable domain handles for all three families |
| Point/vector algebra | `vector + vector` and `vector * scalar` currently return `point3`; `point - point` returns `vector3` | Treat the first two as historical defects and enforce the accepted algebra |
| Triangulation | `triangulate_face` advertises `LazyObjectShape`, resolves to structured data, fails its own `.unlazy()` validator, and generic expansion converts tuples to lists | Replace with a truthful structured mesh/result type and type-preserving container resolution |
| Cache identity | Equal operation graphs have equal hashes; shape values round-trip through the directory cache | Preserve deterministic identity and round-trip semantics, not the old hash bytes or namespace |
| Native materialization | `.unlazy()` changes the runtime type; native OCP accessors force evaluation | Keep only explicit, documented boundaries; compatibility `.unlazy()` returns the same public domain type |
| User `@lazy` | Custom functions return generic `LazyObject`; evaluation recursively expands containers and converts tuples to lists | Keep a bounded legacy adapter and provide a typed extension surface with type-preserving containers |

Expected historical defects are named explicitly in characterization tests so
that later fixes are reviewed as intentional baseline updates rather than
silent regressions.

## Stage 2: evalcache substrate

Status: complete in the current evalcache API. The decorator-first layer is
exported directly from `evalcache`; `evalcache.v2` remains a compatibility
import surface, as does the original `LazyObject` API.

Introduce generic `Expression[T]`, evaluation, hashing, cache policies,
cache-store and serializer protocols, type-preserving container resolution,
progress hooks, and a legacy `LazyObject` adapter.

The implemented substrate includes:

- immutable expression nodes with deterministic operation, argument, result,
  and serializer identity;
- explicit deferred/immediate evaluator modes and runtime result validation;
- independent cache read/write policy, namespaced keys, corruption recovery,
  an in-memory store, and an adapter for dict-like stores such as
  `DirCache_v2`;
- custom deterministic hash encoders for application values;
- serializers returning a payload plus named binary artifacts;
- structured progress events;
- a deliberately opaque and temporary `legacy_expression` bridge.

The default pickle serializer is restricted to trusted user cache locations;
applications crossing a trust boundary must supply a non-executable
serializer.

Exit gate: existing evalcache examples work through the compatibility facade,
while new tests exercise expressions without dynamic Python-type imitation.

## Stage 3: internal vertical slice

Status: complete as a private proving ground in `zencad._typed`. Nothing is
re-exported from the public `zencad` root.

Build a non-public ZenCad path that covers:

```python
box -> transform -> boolean -> faces()[0]
    -> center/mass -> dependent scalar/point operation
    -> new shape -> display/export
```

The slice must exercise `Shape`, a topology subtype, typed sequences,
`Point3`, `Vector3`, `Scalar`, and cache reuse. The public root API remains
unchanged.

Exit gate:

- public classes do not change with evaluation or cache policy;
- the graph survives point and scalar dependencies;
- cache-off performs no disk access;
- fresh-process cache hits work;
- static type checks contain no `Any` in the representative chain;
- benchmark deltas are recorded and acceptable.

This is the primary rollback point: the internal slice can be removed without
changing user code.

### Implemented slice

The representative path now runs as:

```python
from zencad import _typed as typed

runtime = typed.Runtime.deferred(cache=True)
outer: typed.Solid = runtime.box(10)
inner: typed.Solid = runtime.box(4).translate(3, 3, 3)
result: typed.Shape = outer - inner
face: typed.Face = result.faces()[0]
mass: typed.Scalar = result.mass()
center: typed.Point3 = result.center()
offset: typed.Vector3 = typed.Vector3(mass / 1000, center.y, 0)
moved: typed.Shape = result.translate(offset)
native = moved.native()
```

`Shape`, `Solid`, `Face`, `Scalar`, `Point3`, `Vector3`, and
`DeferredSequence[Face]` are stable classes in all four combinations of
immediate/deferred evaluation and cache on/off. Handles from different
runtimes cannot be mixed accidentally. `faces()[0]` adds an expression node
without evaluating the graph; `len(faces)` and iteration are declared
materialization boundaries.

Resolved Shape values use a non-executable serializer whose cache record holds
only version metadata and a named `shape.brep` artifact. No OCP object is
stored in the record. The topology collection itself is not persisted;
individual indexed `Face` results use the same validated BREP path. Cache-off
constructs the evaluator without a store, so it cannot touch the configured
directory.

The compatibility adapter was deliberately narrow at the vertical-slice
checkpoint: 15 resolved functions in
`_operations.py` bridge box construction, translation, difference, topology,
mass/center, and the minimum scalar/vector algebra to the current eager
implementation. At that checkpoint the private production package was 647
lines and its runtime and subprocess tests were 226 lines. As an inventory signal, the current
ZenCad tree still contains 91 legacy lazy decorators across 19 modules and 34
`LazyObject`/`LazyObjectShape` references. A full migration is therefore a
systematic API conversion, not a small facade rename; the next work remains
split between value algebra and Shape/topology cards.

### Verification and measurements

On 2026-08-30 the following gates passed:

- `pytest -q`: 186 tests;
- `uvx mypy --strict --follow-imports=silent --disallow-any-expr
  utest/typecheck/typed_vertical_slice.py`: no issues in the representative
  domain chain;
- a two-process `DirCache_v2` test: the second process reports a cache hit and
  no cache store;
- BREP export/decode from the explicit `native()` boundary in every policy
  combination;
- an isolated wheel build/install smoke containing all `zencad._typed`
  modules;
- Ruff and `compileall` checks for the new package and tests.

The OCP-native return itself is excluded from the no-`Any` static assertion
because the installed OCP distribution provides no mypy stubs; that explicit
boundary is covered at runtime as `TopoDS_Shape`.

A local cache-off microbenchmark used one warm-up and 15 samples of the whole
representative chain, including final Shape and Face materialization:

| Runtime | Median | p95 |
| --- | ---: | ---: |
| legacy deferred | 1.198 ms | 1.339 ms |
| legacy onplace | 2.869 ms | 2.915 ms |
| typed deferred | 3.088 ms | 3.147 ms |
| typed immediate | 3.110 ms | 3.148 ms |

The relevant comparison is against the eager resolved path: the prototype is
about 8% slower in this tiny chain. These numbers are architectural evidence,
not a stable CI performance threshold; broader operations will be dominated by
OCP work and need a dedicated benchmark suite during public cutover.

## Stage 4: value algebra

Status: complete in the private `zencad._typed` layer for Scalar, 2D/3D
points and vectors, Quaternion, and Transform. The implementation remains an
internal proving ground and is not re-exported from the public `zencad` root.

This stage implements immutable scalar, point, vector, quaternion, transform,
and required 2D value types. It defines exact result types for arithmetic,
coercion from Python literals and tuples, comparison/materialization rules,
NumPy conversion, and expression-aware numeric helpers.

Exit gate: algebra property tests and static type tests agree; vector
operations never silently produce points, and immediate-only arithmetic avoids
unnecessary expression nodes.

### Algebra contract

The implemented result table is independent of evaluation and cache policy:

| Operation | Result |
| --- | --- |
| `Scalar op Scalar/literal` | `Scalar` |
| `Vector + Vector`, `Vector - Vector` | same-dimensional `Vector` |
| `Point + Vector`, `Vector + Point` | same-dimensional `Point` |
| `Point - Vector` | same-dimensional `Point` |
| `Point - Point` | same-dimensional `Vector` |
| `Vector * Scalar`, `Scalar * Vector`, `Vector / Scalar` | same-dimensional `Vector` |
| `Vector.dot(Vector)`, 2D `Vector.cross(Vector)` | `Scalar` |
| 3D `Vector.cross(Vector)` | `Vector3` |
| length, point distance, scalar math helpers | `Scalar` |

`Point + Point` and cross-dimensional operations fail explicitly. Handles are
logically immutable, unhashable, and use composition rather than inheriting
from Python numbers, NumPy, OCP, or evalcache classes. Literal and tuple
constructors require an owning `Runtime` when no component handle can supply
one.

Every operation whose operands are all resolved inexpensive values is folded
directly into another resolved value, even when the runtime policy is
deferred. This path emits no evaluator event and performs no cache access. If
any operand contains an `Expression`, the operation adds a typed expression
node. Under immediate policy, a value derived from geometry is first evaluated
through the configured cache and subsequent inexpensive arithmetic folds from
that resolved result.

The documented materialization boundaries are:

- `float()`, `int()`, `bool()`, and scalar comparisons;
- point/vector equality, `value()`, iteration, and `to_numpy()`;
- `to_ocp()` conversion to `gp_Pnt`, `gp_Vec`, `gp_Pnt2d`, or `gp_Vec2d`;
- ordinary Python `math` functions through `Scalar.__float__()`.

Coordinates remain graph-preserving `Scalar` handles. The expression-aware
helpers `sin`, `cos`, `tan`, `asin`, `acos`, `atan`, `atan2`, `sqrt`, `exp`,
and `log` also preserve the graph.

### Quaternion and Transform contract

`Quaternion` is a rotation type, not an arbitrary four-component vector. Its
resolved value is an immutable canonical unit quaternion in `(x, y, z, w)`
order. Construction normalizes the input and chooses one deterministic sign
for the equivalent `q` and `-q` rotations. The `x`, `y`, `z`, and `w`
properties remain graph-preserving `Scalar` handles.

`Transform` is an immutable similarity transformation with the exact model

```text
p' = s R(p) + t
```

where `s` is a finite signed uniform scale whose magnitude exceeds OCP's
minimum representable transform scale, `R` is a `Quaternion` rotation, and `t`
is a `Vector3` translation. A signed scale together with a proper rotation
represents the `gp_Trsf` family, including plane mirrors, without admitting
shear or non-uniform scale. Arbitrary affine transformations will use a
separate future type rather than weakening the invariants of `Transform`.

Application has exact domain results: `Transform.apply(Point3)` and
`transform(point)` return `Point3`, while the corresponding `Vector3`
operations return `Vector3`. Translation affects points but not vectors:
vectors follow `v' = s R(v)`. A transform can therefore never silently erase
the distinction between positions and directions.

Composition follows the existing mathematical and OCP order. For both
rotations and transforms, `outer * inner` applies `inner` first and `outer`
second. The fluent spelling reverses that visual order deliberately:
`first.then(second) == second * first`. Transform composition is exact in the
representation:

```text
s = s_outer * s_inner
R = R_outer * R_inner
t = t_outer + s_outer R_outer(t_inner)
```

Inverse, quaternion rotation, and composition preserve the same domain handle
classes in every evaluator and cache policy.

`Quaternion.rotate(Vector3)` returns `Vector3`, and
`Quaternion.to_transform()` lifts the rotation without changing its graph.
The `Transform.scale`, `Transform.rotation`, and `Transform.translation`
properties return `Scalar`, `Quaternion`, and `Vector3` handles respectively;
reading those properties is not a materialization boundary.

The private constructor surface currently consists of:

- `Quaternion(x, y, z, w, runtime=...)`, its four-element tuple form,
  `Quaternion.identity(runtime=...)`, `Runtime.quaternion(...)`, and
  `Runtime.quaternion_axis_angle(axis, angle)` with the angle in radians;
- `Transform(runtime=...)` and `Runtime.identity_transform()`;
- `Runtime.translation(Vector3)` or `Runtime.translation(x, y, z)`;
- `Runtime.rotation(Quaternion)` or `Runtime.rotation(axis, angle)`;
- `Runtime.scale(factor, center=Point3 | None)`;
- `Runtime.mirror(normal, origin=Point3 | None)`, where the arguments describe
  a plane.

Cheap operations with only resolved inputs fold directly to immutable
`QuaternionValue` and `TransformValue` values. A `Scalar`, `Point3`, or
`Vector3` backed by an `Expression` instead contributes its node to the typed
graph; the returned object is still `Quaternion` or `Transform`. This includes
axis-angle construction, translation, centered scale, mirrors, composition,
inverse, and point/vector application.

Quaternion `value()` and Transform `matrix()` are Python materialization
boundaries. `matrix()` returns a conventional homogeneous 4-by-4 matrix.
`to_ocp()` returns a fresh mutable `gp_Quaternion` or `gp_Trsf`; `from_ocp()`
copies a native value into the immutable representation. OCP types do not
become domain handles and never live inside an expression node.

The private `Shape.transform(Transform)` adapter retains both the shape and
transform dependencies in one typed expression and materializes the OCP
transformation only inside the resolved operation. `transform()` and
`translate()` preserve the concrete topology handle subtype, so transforming
a `Solid` still returns a `Solid`. This is the integration point for the
broader Shape migration, not a public API cutover.

Verification on 2026-08-30 after the Quaternion/Transform checkpoint:

- `pytest -q`: 213 tests, including the four policy combinations, result-type
  tables, algebraic identities, boundaries, invalid operations, and folding;
- strict mypy with `--disallow-any-expr`: all three representative
  type-contract files pass;
- literal folding is checked with zero evaluator events and zero cache-store
  accesses;
- dependent scalar math is checked from `Shape.mass()` through deferred and
  immediate runtimes;
- the built wheel contains the value and transform modules and passes an
  isolated installed algebra/OCP/Shape-transform smoke.

The completed Quaternion/Transform gate additionally covers exact result
types, composition order, identities and inverses, point-versus-vector
semantics, mirrors and centered scales, invalid values, OCP round trips,
resolved folding, deferred dependencies, the four evaluation/cache policy
combinations, and `Shape.transform`. The strict result table in
`utest/typecheck/typed_transform.py` uses `--disallow-any-expr`; native OCP
returns remain runtime-tested boundaries because the installed OCP package
does not provide mypy stubs.

## Stage 5: shape and topology

Status: complete in the private `zencad._typed` layer. The topology-handle
core, uniform topology-query surface, representative precise factories, and
binary boolean surface are implemented. The public root API remains unchanged.

Introduce `Shape` and precise topology handles, typed topology sequences,
resolved OCP adapters, result validators, BREP codecs, and materializing native
accessors. Extend the existing typed `Shape.transform(Transform)` adapter while
migrating primitives, booleans, topology reflection, and heavy shape
operations behind the typed layer.

Exit gate: representative models require no `LazyObjectShape` or
`evalcache.unlazy_if_need()` in the typed path, and topology declarations are
validated when resolved.

### Topology-handle contract

`Shape` is the conservative general shape handle. The eight precise topology
handles are direct `Shape` subtypes: `Vertex`, `Edge`, `Wire`, `Face`, `Shell`,
`Solid`, `Compound`, and `CompSolid`. Every handle contains either a validated
resolved shape snapshot or its typed expression; neither state is exposed as
an `evalcache` proxy. Evaluation and cache policy therefore do not change the
class visible to the caller.

Operations advertise only the precision they can guarantee:

- `Runtime.box(...)` and `Runtime.sphere(...)` return `Solid`;
- `Runtime.segment(...)` returns `Edge`;
- `Runtime.polysegment(...)` returns `Wire`;
- `Runtime.polygon(...)` and `Runtime.rectangle(...)` return `Face`;
- `transform()` and `translate()` preserve the receiver's precise topology
  subtype;
- binary union (`+`), difference (`-`), and intersection (`^`) conservatively
  return `Shape`, because a boolean can change topology kind;
- `Vertex.point()` returns the geometric position as `Point3` without
  conflating a topological vertex with a coordinate value.

Factory arguments remain part of the typed graph. Box dimensions, sphere
radius, and rectangle dimensions accept `Scalar` dependencies; `box()` also
accepts a `Vector3` size. Segment, polysegment, and polygon accept `Point3`
handles, including points derived from deferred geometry and vector algebra.
No factory converts a handle through `float()`, tuple iteration, or an OCP
accessor while constructing the graph. The private `box()` contract accepts
one scalar for a cube, three scalar dimensions, or one `Vector3`; the ambiguous
two-dimension legacy spelling is deliberately rejected.

All three boolean operators use the general `Shape` ResultSpec and BREP codec.
This keeps their declaration truthful even when OCCT produces a solid,
compound, or a non-null empty compound. A fresh-runtime cache hit for the
boolean result restores the final BREP without evaluating either input graph.

The OCP boundary has explicit ownership. `from_ocp()` takes a deep-copy
snapshot and validates it against the requested handle class; `native()`
returns a fresh deep-copy snapshot, so mutating the returned OCP object cannot
mutate the handle's resolved value. The private `_legacy()` escape hatch is a
borrowed compatibility boundary for existing eager implementation adapters.
It is intentionally not part of the normal typed contract and must not leak
into user-facing code. The bounded `.unlazy()` compatibility spelling
materializes and returns the same precise handle; `native()` remains the
explicit owned OCP snapshot boundary. No public `.Shape()` alias is introduced
inside the private layer.

All eight topology queries now return a `DeferredSequence` whose element type
matches the requested topology kind:

- `vertices() -> DeferredSequence[Vertex]`;
- `edges() -> DeferredSequence[Edge]`;
- `wires() -> DeferredSequence[Wire]`;
- `faces() -> DeferredSequence[Face]`;
- `shells() -> DeferredSequence[Shell]`;
- `solids() -> DeferredSequence[Solid]`;
- `compounds() -> DeferredSequence[Compound]`;
- `compsolids() -> DeferredSequence[CompSolid]`.

In deferred mode, indexing, including a negative index, adds a typed item
expression without evaluating the sequence. `len(sequence)` and consumption
through iteration are explicit materialization boundaries for the query tuple.
In immediate mode, query and item expressions evaluate when constructed, as
required by that policy. The tuple expression is deliberately
`cacheable=False`: persisting an intermediate collection of OCP values would
require a separate collection format without improving the normal indexed
path. Each indexed item expression is independently cacheable and uses the
precise topology handle's validated BREP serializer. A cache hit for an item
can therefore restore that item without recomputing or persisting the query
tuple.

`vertices()` is the one intentional departure from the legacy query
semantics. It returns values unique by OCCT `IsSame` identity: the underlying
TShape and Location participate in identity, while Orientation does not.
Consequently, different TShapes at the same geometric coordinate remain two
vertices, and occurrences of one TShape at different Locations remain two
vertices. The order is the order of each identity's first topology-traversal
occurrence. This is deterministic for that shape traversal, but is not a
stable topological-naming guarantee across modeling operations. Callers that
need coordinates obtain them explicitly with `Vertex.point()`.

The other seven queries intentionally retain the legacy `TopExp_Explorer`
occurrence semantics. They do not globally deduplicate shared subshapes; for
example, a box reports 24 edge occurrences rather than 12 unique edges. When
the queried root already has the requested kind, the root is included and
nested shapes of that same kind are not traversed. This behavior is part of
the migration contract rather than an accidental consequence of the typed
wrapper.

Verification on 2026-08-30 after the completed Shape/topology stage:

- `pytest -q`: 239 tests;
- strict mypy with `--disallow-any-expr`: all five representative typed
  contracts pass, including precise factory and boolean result types;
- runtime tests cover exact `Solid`/`Face`/`Wire`/`Edge` factories and all
  binary booleans in the immediate/deferred × cache on/off matrix;
- graph tests feed deferred `Scalar`, `Point3`, and `Vector3` dependencies into
  factories without early materialization;
- fresh-runtime cache tests restore the final boolean BREP directly, while a
  representative creation → transform → boolean → topology → value → native/
  export chain contains no `LazyObjectShape`;
- an isolated wheel build/install smoke executes every representative factory
  and boolean outside the source checkout;
- Ruff, formatting, `compileall`, and diff-integrity checks pass.

The next migration gate is Stage 6: remaining geometry and runtime boundaries.

Verification on 2026-08-30 after the complete topology-query checkpoint:

- `pytest -q`: 231 tests;
- strict mypy with `--disallow-any-expr`: all four representative typed
  contracts pass, including all eight `DeferredSequence[T]` query results;
- runtime tests cover exact query types and counts in all four evaluation/
  cache policy combinations, deferred indexing boundaries, `IsSame` identity
  and traversal order, cache hit/rejection behavior, and graph-aware
  `Vertex.point()`;
- an isolated wheel build/install smoke executes all eight typed topology
  queries outside the source checkout, alongside the headless geometry/I/O
  smoke;
- Ruff, formatting, `compileall`, and diff-integrity checks pass.

Verification on 2026-08-30 after the topology-core checkpoint:

- `pytest -q`: 220 tests;
- strict mypy with `--disallow-any-expr`: all four representative typed
  contracts pass, including every topology handle subtype;
- runtime tests cover all eight handles, all four evaluation/cache policy
  combinations, exact native OCP classes, topology validators, subtype-
  preserving transforms, and BREP snapshot mutation isolation;
- an isolated wheel build/install smoke imports `zencad._typed.topology` and
  executes the typed `Solid -> Face` path outside the source checkout;
- Ruff, formatting, `compileall`, and diff-integrity checks pass.

## Stage 6: remaining geometry and boundaries

Status: complete for the connected private typed kernel. The private `Curve`,
`Curve2`, representative `Surface`/sweep-law,
`BoundaryBox`/structured-range, `MeshData`, and remaining-geometry integration
gates are complete. Full compatibility with every legacy factory, operation,
and method is tracked separately by the Stage 7 parity contract.

Migrate curves, 2D curves, surfaces, sweep laws, boundary boxes, triangulation,
mesh values, conversion, display, scene transport, and file artifacts.

Exit gate: every normal geometry result belongs to a documented domain type;
all materialization boundaries are explicit and covered by tests.

### Curve and Curve2 contract

`Curve` and `Curve2` are stable handles containing either an immutable curve
snapshot or an `Expression` that produces one. They do not inherit from OCP or
`evalcache.LazyObject`, and their visible class does not depend on immediate/
deferred evaluation or cache policy. This checkpoint remains private under
`zencad._typed`; the legacy public curve API has not changed.

The representative construction surface is:

- `Runtime.line(Point3, Vector3)`, `circle(ScalarInput)`, and
  `ellipse(major, minor)`, returning `Curve`;
- `Runtime.segment2(Point2, Point2)` and `ellipse2(major, minor)`, returning
  `Curve2`;
- `Runtime.trim_curve2(curve, start, end)` and `Curve2.trim(start, end)`,
  preserving `Curve2`.

All point, direction, radius, and trim arguments remain expression-aware.
`point(parameter)` returns `Point3` or `Point2`; `tangent(parameter)` returns
the OCCT first derivative as `Vector3` or `Vector2`; and `range()` returns a
named `Interval` containing graph-preserving `Scalar` bounds. Reading those methods does not
materialize a deferred upstream graph. Calling `value()` on the returned
point/vector, converting a range endpoint to `float`, `native()`, or
`.unlazy()` is an explicit materialization boundary.

The resolved representation is not a mutable OCP handle. It is frozen bytes
written by OCCT's full-precision `GeomTools_CurveSet` or
`GeomTools_Curve2dSet` set format, with a family-specific deterministic
evalcache key. `from_ocp()`
captures that snapshot immediately; `native()` decodes a fresh OCP object on
every call. Mutating either the source object or a returned native object
therefore cannot alter the typed handle.

Persistent cache records use distinct non-executable serializers and named
`curve.geom` / `curve2.geom` artifacts. Payload tags, serializer IDs, result
type IDs, and validators prevent a 2D curve record from being accepted as a
3D curve or vice versa. Corrupt or wrong-family records are rejected and
recomputed by evalcache's normal recovery path.

The original Curve checkpoint briefly used the single-item compact writer,
which rounds geometry to roughly six significant decimal digits. The Surface
checkpoint exposed that loss on generated BSpline poles. Curve and Curve2 now
use version-2 full-precision set codecs; their old disposable cache records
are rejected by changed result, serializer, payload, and value-key versions.
A regression test preserves non-round decimal locations and radii through all
three native snapshot families.

Verification on 2026-08-30 after the Curve/Curve2 checkpoint:

- `pytest -q`: 245 tests;
- strict mypy with `--disallow-any-expr`: all six representative typed
  contracts pass;
- runtime tests cover exact handle and query result types in the four
  evaluation/cache policy combinations, graph-aware scalar/point/vector
  inputs, input validation, owned OCP snapshots, and bounded `.unlazy()`;
- cache tests cover family-specific artifacts, wrong-family rejection,
  fresh-runtime hits, and persistent reuse by a fresh process;
- the installed-wheel smoke exercises both curve families outside the source
  checkout.

### Surface and sweep-law contract

`Surface` follows the same stable-handle and immutable-snapshot model as
`Curve`. `Runtime.cylinder_surface(radius)` is the representative analytic
factory. `point(u, v)` returns `Point3`, `normal(u, v)` returns a unit
`Vector3`, `u_range()` and `v_range()` return named graph-preserving
`Interval` records, and `u_iso(parameter)` / `v_iso(parameter)` return `Curve`.
No query exposes a generic evalcache proxy.

The sweep-law contract is an immutable composition rather than a public OCP
object graph. `Runtime.constant_sweep_scale(scale, domain)` returns a frozen
`SweepScaleLaw` containing a graph-preserving `Scalar` and explicit `Interval`.
`Runtime.evolved_sweep_section(curve, scale_law)` combines it with a `Curve` as
`SweepSectionLaw`; `Runtime.sweep_location(spine, trihedron)` combines a spine
with `SweepTrihedron` as `SweepLocationLaw`. These three records replace the
legacy `LawFunction`, `LawSection`, and `LawLocation` wrappers, while the enum
replaces `LawTrihedron` and its two public factories.

Laws are construction descriptions, not independently materializable results:
they expose no `native()` boundary and create no cache records or codecs of
their own. `Runtime.sweep_surface_from_laws(section, location, ...)` unpacks
their constituent expression states into the terminal `Surface` operation.
Evalcache therefore hashes the exact curve, scalar, domain, and enum inputs;
only the resulting immutable `Surface` snapshot is serialized. A future law
family must add another closed declarative variant and a resolved OCCT
materializer. Arbitrary mutable OCP laws and opaque Python callbacks are not a
supported fallback because neither has truthful ownership, hashing, or
cross-process cache semantics.

`Runtime.sweep_surface(section, spine, ...)` remains the concise spelling. It
composes the same law values internally, using the spine parameter range for
the scale-law domain. Tolerance, requested continuity, maximum degree, and
maximum segment count are validated construction options. The resolved
operation alone creates `Law_Constant`, `GeomFill_EvolvedSection`, the
trihedron/location laws, and `GeomFill_Sweep`; a trimmed-spine regression test
makes the default domain choice observable.

Topology sweeps use a separate explicit option algebra. `PipeTrihedron`
replaces the legacy string-to-OCCT `geomfill_triedron_map` and names all ten
accepted builder modes. `PipeTransition` replaces the integer transition
flags. `Runtime.pipe()` returns a general `Shape` because OCCT's result kind
depends on the profile, while `Runtime.pipe_shell()` returns an exact `Solid`
or `Shell` from its `solid` policy. Its Frenet, binormal, parallel, and discrete
orientation modes are mutually exclusive instead of silently overriding one
another. `Runtime.sweep()` is only the characterized single-profile solid
compatibility spelling.

Binormal and parallel pipe-shell modes also repair a legacy boundary bug: the
old code called a nonexistent `vector3.Dir()` method. Both paths now construct
an owned `gp_Dir` explicitly, and legacy plus typed regressions exercise them.
`Runtime.revol2()` retains the documented radius, section-count, yaw, roll,
and multipart approximation controls, but returns an exact `Solid` instead of
the legacy lazy wrapper. Scalar interval bounds remain graph operands and the
resolved boundary rejects empty/non-finite sweeps and undersampled parts.

Resolved surfaces are full-precision `GeomTools_SurfaceSet` bytes with a
deterministic value key. `Surface.from_ocp()` captures an owned snapshot and
`native()` reconstructs a fresh mutable `Geom_Surface` on every call. The
family-specific non-executable cache record contains one `surface.geom`
artifact and rejects Curve artifacts, wrong payloads, and invalid surfaces.

Verification on 2026-08-30 after the Surface/sweep checkpoint:

- `pytest -q`: 252 tests;
- strict mypy with `--disallow-any-expr`: all seven representative typed
  contracts pass;
- the immediate/deferred × cache on/off matrix covers analytic and swept
  surfaces, typed queries, iso-curves, both trihedron choices, graph-aware
  Scalar/Curve inputs, validation, and bounded `.unlazy()`;
- cache tests cover non-pickle artifacts, wrong-family rejection,
  fresh-runtime reuse, and persistent reuse by a fresh process;
- full-precision and native ownership tests cover Curve, Curve2, and Surface;
- the installed-wheel smoke exercises cylinder and sweep surfaces outside the
  source checkout.

### BoundaryBox and structured-range contract

`BoundaryBox` is an immutable stable handle containing either six resolved
axis bounds or an expression that produces them. Empty bounds are represented
explicitly rather than by mutable initialization state. `Shape.boundbox()`
and its `bbox()` alias preserve the upstream shape graph;
`Runtime.boundary_box(minimum, maximum)` accepts typed `Point3` corners, and
`Runtime.empty_boundary_box()` provides the identity for `union()`.

Coordinate properties return `Scalar`, `minimum` and `maximum` return
`Point3`, and `size` returns `Vector3`. `center` and all three named axis
ranges remain composable without exposing an evalcache proxy. `is_empty()` is
an intentional materialization boundary because it returns a Python `bool`.
Reading coordinates, corners, center, size, or a materialized record from an
empty box raises `ValueError` instead of manufacturing zero bounds.

`BoundaryBox.value()` returns a frozen `BoundaryBoxRecord`; `native()` returns
a fresh mutable `Bnd_Box` snapshot, including a void native box for an empty
value. Shape-derived coordinates intentionally retain the same OCCT bounding
gap as the legacy `Shape.boundbox()` implementation. Source and returned OCP
objects have no shared mutable ownership with the typed handle.

`Interval` replaces unnamed range tuples on `Curve`, `Curve2`, `Surface`, and
`BoundaryBox`. Its `lower` and `upper` fields are `Scalar` handles,
`length()` remains graph-aware, and `value()` explicitly materializes a fixed
pair of floats. Iteration yields the same two `Scalar` handles for bounded
compatibility, but tuple/list expansion is not the structured public model.

Resolved boundary boxes use a deterministic binary serializer with an
explicit empty marker or six big-endian IEEE-754 doubles. The cache format is
non-executable, has no artifacts, rejects wrong-family payloads, and preserves
full double precision across runtimes and processes.

Verification on 2026-08-30 after the BoundaryBox/structured-range checkpoint:

- `pytest -q`: 260 tests;
- strict mypy with `--disallow-any-expr`: all eight representative typed
  contracts pass;
- the immediate/deferred × cache on/off matrix covers shape-derived bounds,
  named records and ranges, corners, center, size, native conversion, and
  bounded `.unlazy()`;
- graph tests cover bounds built from deferred points and scalars, union with
  shape-derived bounds, and the explicit materialization behavior of empty
  boxes;
- cache tests cover the non-pickle binary payload, wrong-family rejection,
  fresh-runtime hits, and persistent reuse by a fresh process;
- native ownership tests cover non-round double precision, mutable source and
  return isolation, and the explicit void-box representation;
- the installed-wheel smoke exercises `Interval`, `BoundaryBox`, and
  `BoundaryBoxRecord` outside the source checkout.

### MeshData and triangulation contract

`MeshData` is the stable typed replacement for both compact mesh extraction
and the historically misdeclared `triangulate_face()` result. It contains a
frozen, tuple-backed `MeshValue` or an expression producing one; evaluation
policy and cache policy never change the visible handle class.
`Shape.to_mesh(...)` retains the source shape graph, while
`Face.triangulate(...)` provides the truthful face-specific spelling. The
legacy public functions remain unchanged until the atomic public cutover.

The resolved mesh stores finite positions and non-zero normals, valid indexed
triangles, exactly one source face ID per triangle, and the dropped-degenerate
triangle count. Every row and outer collection is a tuple. Meshing controls
such as linear/angular deflection, crease angle, relative mode, parallel mode,
and weld tolerance are eagerly validated policy values rather than hidden
geometry graph inputs.

`value()` returns a frozen `MeshDataRecord`. Collection and count properties
are explicit materialization boundaries because ordinary Python and renderer
consumers need concrete indexed arrays and integer sizes. `boundbox()` remains
composable and returns typed `BoundaryBox` without first exposing mesh rows.
`native()` creates a fresh `Poly_Triangulation`, and `to_numpy()` creates fresh
arrays in a `MeshArrayRecord`; mutating either result cannot affect the handle.

The full-fidelity cache serializer uses a versioned binary `mesh.bin` artifact
and preserves positions, normals, triangles, face provenance, and dropped
counts. Its binary layout uses big-endian IEEE-754 doubles and fixed-width
indices and rejects wrong-family, truncated, invalid, and size-inconsistent
records. `display_payload()` is a separate explicit adapter to the existing
scene mesh protocol. That protocol intentionally carries render geometry but
not modeling provenance; the typed cache does not inherit that information
loss.

Verification on 2026-08-30 after the MeshData/triangulation checkpoint:

- `pytest -q`: 267 tests;
- strict mypy with `--disallow-any-expr`: all nine representative typed
  contracts pass;
- the immediate/deferred × cache on/off matrix covers shape and face mesh
  extraction with one stable result class and tuple-only materialized records;
- graph and validation tests cover deferred shape transforms, meshing policy
  controls, indexed geometry invariants, face provenance, and typed bounds;
- native and NumPy ownership tests cover source mutation, fresh returned
  snapshots, and non-round double precision;
- cache tests cover the deterministic full-fidelity artifact, corrupt-family
  rejection, fresh-runtime hits, and persistent reuse by a fresh process;
- the current scene mesh transport round-trips typed render geometry through
  the explicit display adapter;
- the installed-wheel smoke exercises `Shape.to_mesh()`,
  `Face.triangulate()`, `MeshDataRecord`, and display transport outside the
  source checkout.

### Remaining-geometry integration contract

The private typed slice now forms one connected domain graph. Topology reaches
geometry through `Edge.curve()` and `Face.surface()`, while every `Shape`
reaches `BoundaryBox` and `MeshData`. Extracted edge curves are snapshotted as
`Geom_TrimmedCurve` over the edge's actual BRep parameter range rather than as
an accidentally infinite basis curve. Extracted face surfaces are
`Geom_RectangularTrimmedSurface` snapshots over the face's finite UV bounds.
The latter represents the parametric support rectangle; topology trimming
wires remain the responsibility of the `Face` handle.

A representative deferred chain can therefore derive a shape from typed
scalars, index its typed edge and face sequences, obtain `Curve` and `Surface`,
and compose bounds and mesh extraction without materializing any intermediate
or exposing an evalcache proxy. Immediate/deferred evaluation and cache on/off
produce the same classes throughout this chain.

Every name in `zencad._typed.__all__` resolves exactly once. Runtime tests
check every representative handle, structured record, and materialized value
against legacy `evalcache.LazyObject`; none inherits from or is an instance of
that proxy family. `Expression` remains visible only in private implementation
state and evaluator plumbing.

The integration cache gate evaluates Curve, Surface, BoundaryBox, and MeshData
from one topology graph, then reconstructs the graph in a fresh `Runtime` and
observes family-specific cache hits for all four results. Existing persistent
fresh-process tests retain coverage of each serialized family, and the
installed-wheel gate repeats the connected edge/face/bounds/mesh path outside
the checkout.

Verification on 2026-08-30 after the remaining-geometry integration gate:

- `pytest -q`: 271 tests;
- strict mypy with `--disallow-any-expr`: all ten representative typed
  contracts pass, including the complete connected domain chain;
- runtime policy tests cover `Solid → Edge → Curve`,
  `Solid → Face → Surface`, `Shape → BoundaryBox`, and `Shape → MeshData` in
  all four immediate/deferred × cache on/off combinations;
- isolation tests cover all exported representative handles, records, and
  materialized results against the legacy LazyObject hierarchy;
- cache tests observe fresh-runtime hits for all four remaining-geometry
  families from one reconstructed topology graph;
- export, finite curve/UV ranges, mesh-versus-shape bounds, Ruff, formatting,
  compileall, diff integrity, and the installed-wheel chain all pass.

Stage 6 is complete. The private typed proving ground is ready for the
separate public-cutover decision and compatibility audit described by Stage 7.

## Stage 7: public cutover

Status: parity inventory and private family migrations are complete. The
machine-readable source of truth is
[`typed-api-parity.json`](typed-api-parity.json), with rationale and current
counts in [`typed-api-parity.md`](typed-api-parity.md).

First bring the private typed layer to complete functional parity with the
intentionally supported legacy geometry API. Keep the legacy root active
during this work. Only after every missing, partial, and repair row has been
resolved, switch the public geometry API as one coherent change. Keep bounded
compatibility helpers such as `.unlazy()` returning the same domain handle,
selected native accessors, lowercase point/vector aliases, and an explicitly
legacy lazy extension surface.

Exit gate: the parity checker contains only `implemented` or explicitly
`unchanged` rows; the root export contract and legacy signature snapshot are
reviewed; unit, subprocess, example, GUI/headless smoke, cache, performance,
type, and installed-wheel checks pass without requiring `.unlazy()` in
ordinary models.

### Affine transform repair checkpoint

The private typed layer now separates similarity and general affine maps.
`Transform` remains the compact quaternion/uniform-scale domain value backed
by `gp_Trsf`; `AffineTransform` owns a finite immutable row-major 3x4 matrix
and materializes a fresh `gp_GTrsf` only at the OCP boundary. Composition of
either transform family promotes to `AffineTransform` whenever a general map
is involved, while point and vector application retain distinct translation
semantics.

`Runtime.scaleX/Y/Z/XYZ`, the matching `Shape` methods, and the typed
`GeneralTransformation` compatibility alias cover the legacy non-uniform
surface. The cache stores affine matrices as a versioned twelve-double
payload rather than pickling mutable OCP state. Characterization also repairs
the legacy similarity/general-transformation pickle and composition defects,
so existing root users do not retain half-initialized native transforms while
the root cutover is pending.

### Modeling operations and geometry-query checkpoint

Task #2043 completes every non-sweep row in the sweeps-and-operations family.
Sequence and variadic booleans, boundary sectioning, fillet/chamfer aliases,
offset and thick-solid construction, sewing, solid repair, same-domain
unification, topology restoration, and triangulation compatibility all retain
stable typed handles. Results use the most precise truthful topology subtype;
operations whose topology can change continue to return general `Shape`.

Nearest-topology queries return the requested `Vertex`, `Edge`, `Wire`,
`Face`, `Shell`, `Solid`, `CompSolid`, or `Compound` handle. Curve projection
returns `CurveProjection`, a named record of typed point, parameter, and
distance handles. Mesh node and triangle compatibility produces immutable
numeric tuples and normalizes triangle indices to zero-based rows.

Verification on 2026-08-31 after this checkpoint:

- the headless runner passes its isolated 3-test and 13-test groups plus 336
  discovered tests;
- strict mypy with `--disallow-any-expr` passes all 15 representative typed
  contracts;
- the parity inventory reports 341 implemented, 27 missing, 3 partial, 6
  repair, and 3 unchanged rows; all 16 missing rows in this family are owned
  by the separate sweep and sweep-law tasks;
- immediate/deferred × cache on/off matrices cover booleans, offset and
  thick-solid construction, unification, and nearest-topology results;
- a clean wheel using the local evalcache checkout passes the installed
  geometry/I/O smoke outside the source tree, including the new boolean,
  section, offset, unification, nearest-topology, and projection APIs.

### Mesh, conversion, and display checkpoint

Task #2044 completes the mesh-convert-display parity family. Typed Runtime
adapters cover BREP, STL, and SVG file/string boundaries; BREP and SVG imports
return stable `Shape` snapshots, and exports isolate mutable native data from
the source handle. `MeshData` provides a compatibility spelling for fresh
native triangulation conversion.

Managed and direct scenes accept typed `Shape`, `MeshData`, and `Point3`.
Managed drafts retain typed sources until snapshot encoding, while direct
scenes materialize only when constructing an interactive renderer object. The
headless path does not import Qt. Legacy point, shape, mesh, assembly, and
display behavior remains covered alongside the typed adapters.

Verification on 2026-08-31 after this checkpoint:

- the headless runner passes its isolated 3-test and 13-test groups plus 344
  discovered tests;
- strict mypy with `--disallow-any-expr` passes all 15 representative typed
  contracts;
- the parity inventory reports 355 implemented, 16 missing, 0 partial, 6
  repair, and 3 unchanged rows; mesh-convert-display has no open rows;
- BREP round-trips pass all four immediate/deferred × cache on/off policies,
  and STL/SVG/mesh compatibility and managed/direct scene tests pass;
- a clean wheel using the local evalcache checkout passes the installed smoke
  outside the source tree, including typed scene snapshot transport.

### Sweep and sweep-law checkpoint

Tasks #2036 and #2042 complete the final missing parity family. Immutable
`SweepScaleLaw`, `SweepSectionLaw`, and `SweepLocationLaw` descriptions retain
their typed graph operands until terminal surface evaluation. Topology
extrusion, revolution, loft, pipe, pipe-shell, single-profile sweep, and rolled
revolution all return stable domain handles. Literal policies select exact
`Solid`/`Shell` results where OCCT topology is knowable; ordinary pipe and
extrusion/revolution remain general `Shape` where the profile controls the
result kind.

Verification on 2026-08-31 after this checkpoint:

- the headless runner passes its isolated 3-test and 13-test groups plus 351
  discovered tests;
- strict mypy with `--disallow-any-expr` passes all 15 representative typed
  contracts;
- the parity inventory reports 371 implemented, 0 partial, 0 missing, 6
  explicitly characterized repair, and 3 unchanged rows;
- the immediate/deferred x cache on/off matrix covers all topology sweep
  families, all ten pipe trihedron modes, every pipe transition, immutable
  surface laws, validation, and exact result classes;
- shared-store and fresh-process tests observe cache hits for typed revolution
  graphs, including the multipart rolled-revolution path;
- the parity checker, Ruff F checks, compileall, and diff integrity pass;
- a clean wheel built with the local evalcache checkout passes the installed
  smoke outside the source tree with laws, extrusion, revolution, loft, pipe,
  pipe-shell, and `revol2` exercised.

### Decorator-owned operation extraction checkpoint

Task #2052 starts dismantling the typed `Runtime` as an operation container.
`zencad.operation` now has two deliberately separate forms:

- bare `@zencad.operation` delegates to the historical `lazy` implementation,
  so existing extension functions retain their current dynamic behavior;
- configured `@zencad.operation(backend=..., result=..., returns=...)`
  declares a typed domain operation over the current top-level evalcache API.

The configured decorator lowers nested ZenCad handles to expression state,
selects their common evaluator context, rejects mixed runtimes, applies an
explicit literal-folding policy, and wraps the result in a stable domain
handle. `typed.box` was the first complete module-level declaration in
`_typed/solid.py`; representative scalar addition and Shape union declarations
prove value folding and method forwarding without keeping their operation
construction in `Runtime`.

Task #2050 then moves the complete solid-primitive family: `box`/`cube`,
`sphere`, `cylinder`, `cone`, `torus`, `halfspace`, and `make_solid` are
module-level typed entry points. Their resolved implementations live in
`_solid_operations.py`, argument normalization lives in `solid.py` and
`values.py`, and the corresponding `Runtime` methods are compatibility
forwarders only. This removes both expression construction and resolved CAD
implementation from `Runtime` for the whole family. `empty_shape` remains in
the next topology extraction rather than being misplaced with solid
primitives.

The next #2050 child extracts the topology algebra. Module-level
`empty_shape`/`nullshape`, `union`, `intersect`/`intersection`, `difference`,
and `section` declarations live in `_typed/booleans.py`, with resolved OCCT
implementations in `_boolean_operations.py`. Binary `Shape` operators delegate
to private declarations in the same module and retain the established
`zencad.typed.shape.union`, `.difference`, and `.intersection` identities.
`section` owns its plane-operand normalization but temporarily composes the
still-unmigrated transform entry points through the selected Runtime context.
All corresponding Runtime methods are forwarding shims.

The public root `zencad.box` is intentionally not switched independently:
doing that before the neighboring transforms, booleans, and queries move would
create a mixed legacy/typed object graph. Public replacement proceeds by a
coherent operation family after its module-level declarations are complete.
Examples that own custom operations now use `@zencad.operation`, while
`@lazy` remains tested and supported.

No evalcache change is required for this checkpoint. ZenCad consumes
`evalcache.operation`, `ResultSpec`, `Expression`, `Evaluator`, and related
types from the canonical top-level package; a future evaluator-binding helper
could reduce adapter plumbing but is not a migration blocker.

Verification on 2026-08-31 after this checkpoint:

- all 375 tests pass;
- strict mypy with `--disallow-any-expr` passes all 16 representative typed
  contracts;
- the decorator tests cover module declaration, Runtime forwarding, operation
  identity, immediate literal folding, cross-runtime rejection, and both bare
  compatibility decorators.

## Stage 8: typing and cleanup

Publish `py.typed`, overload flexible constructors, type-check representative
models, document extension APIs, and then remove compatibility surfaces on the
chosen release schedule.

The distribution decision—new incompatible ZenCad major or a separate
`zencad2` repository—is made after the vertical slice and compatibility audit,
not before.

## Cross-cutting rules

- Public domain handles use composition, not inheritance from evalcache,
  built-in numeric types, NumPy arrays, or OCP types.
- Evaluation mode never changes a public result class.
- Lazy and cache policies remain independent.
- Expressions and resolved domain values are logically immutable.
- Cache schema changes use a new namespace rather than migrating disposable
  entries.
- Do not migrate public factories one by one into a mixed return-type API.
- Every stage retains a runnable gate and an explicit rollback point.
