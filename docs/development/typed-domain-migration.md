# Typed domain migration

> Status: in progress. The characterization baseline, evalcache v2 substrate,
> private typed vertical slice, Scalar/Point/Vector/Quaternion/Transform
> algebra, the topology-handle core, and the complete typed topology-query
> surface are implemented; no public typed-domain cutover described here is
> implemented yet. The accepted direction and rationale are recorded in
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

## Stage 2: evalcache v2 substrate

Status: complete on the evalcache `v2` branch. The additive public layer is
exported from `evalcache.v2` while the original `LazyObject` API remains
available unchanged.

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

Status: in progress in the private `zencad._typed` layer. The topology-handle
core and the uniform topology-query surface are implemented. The broader
Shape factory/boolean migration remains the next separate gate.

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

- `Runtime.box(...)` returns `Solid`;
- `transform()` and `translate()` preserve the receiver's precise topology
  subtype;
- boolean difference conservatively returns `Shape`, because a boolean can
  change topology kind;
- `Vertex.point()` returns the geometric position as `Point3` without
  conflating a topological vertex with a coordinate value.

The OCP boundary has explicit ownership. `from_ocp()` takes a deep-copy
snapshot and validates it against the requested handle class; `native()`
returns a fresh deep-copy snapshot, so mutating the returned OCP object cannot
mutate the handle's resolved value. The private `_legacy()` escape hatch is a
borrowed compatibility boundary for existing eager implementation adapters.
It is intentionally not part of the normal typed contract and must not leak
into user-facing code.

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

The next Stage 5 gate is the broader typed Shape factory and boolean surface;
it remains separate from the completed topology-query work.

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

Migrate curves, 2D curves, surfaces, sweep laws, boundary boxes, triangulation,
mesh values, conversion, display, scene transport, and file artifacts.

Exit gate: every normal geometry result belongs to a documented domain type;
all materialization boundaries are explicit and covered by tests.

## Stage 7: public cutover

Switch the public geometry API as one coherent change. Keep only bounded
compatibility helpers: `.unlazy()` returning the same materialized domain
type, selected native accessors, lowercase point/vector aliases, and an
explicitly legacy lazy extension surface.

Exit gate: unit, subprocess, example, GUI/headless smoke, cache, performance,
and installed-wheel checks pass without requiring `.unlazy()` in ordinary
models.

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
