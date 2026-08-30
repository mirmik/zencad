# Typed domain migration

> Status: in progress. The characterization baseline and evalcache v2
> substrate are implemented; no public typed-domain cutover described here is
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
          +--> Scalar/Point/Vector/Transform algebra
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

## Stage 4: value algebra

Implement immutable scalar, point, vector, transformation, and required 2D
value types. Define exact result types for arithmetic, coercion from Python
literals and tuples, comparison/materialization rules, NumPy conversion, and
expression-aware numeric helpers.

Exit gate: algebra property tests and static type tests agree; vector
operations never silently produce points, and immediate-only arithmetic avoids
unnecessary expression nodes.

## Stage 5: shape and topology

Introduce `Shape` and precise topology handles, typed topology sequences,
resolved OCP adapters, result validators, BREP codecs, and materializing native
accessors. Migrate primitives, transformations, booleans, topology reflection,
and heavy shape operations behind the typed layer.

Exit gate: representative models require no `LazyObjectShape` or
`evalcache.unlazy_if_need()` in the typed path, and topology declarations are
validated when resolved.

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
