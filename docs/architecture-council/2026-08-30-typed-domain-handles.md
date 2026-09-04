# Typed domain handles and an internal lazy graph

- Date: 2026-08-30
- Status: Accepted
- Kanboard: #2007 “[typing] Спрятать lazy-граф внутри domain types”
- Related: #2002, #2005, #2006

## Context

ZenCad currently exposes two runtime type systems. Resolved geometry uses
domain classes such as `Shape`, `Curve`, and `Surface`, while deferred results
use `evalcache.LazyObject` subclasses. Only shapes have a manually maintained
`LazyObjectShape` facade. Shape queries, curves, surfaces, collections, and
scalar results generally fall back to an untyped `LazyObject`.

Consequently, the class returned by the same public function depends on the
global evaluation policy. User scripts and ZenCad internals call `unlazy()`,
`evalcache.unlazy_if_need()`, or mutate `zencad.lazy` directly. Static return
annotations cannot truthfully describe both modes, and manually classifying
proxy methods can disagree with the value actually produced.

The audit found 84 lazy-decorated core operations, six direct
`evalcache.LazyObject` subclasses, and sixteen production modules importing
evalcache. Existing point and vector classes also blur their algebra by
inheriting from `numpy.ndarray`; for example, vector arithmetic can return a
point.

ZenCad and evalcache are being developed on separate migration branches:
`feature/migration` and `v2`, respectively. Evalcache is controlled by the
same project and can evolve together with ZenCad.

## Decision

ZenCad will replace the public lazy-proxy model with typed domain handles.
Each public domain object has one stable runtime type and contains either an
immediate resolved value or an internal `Expression[T]`. Evaluation mode and
cache policy may change the internal state, but never the public class.

The initial lazy-capable domain includes:

- `Scalar`;
- `Point2`, `Vector2`, `Point3`, and `Vector3`;
- transformations and, where useful, quaternion values;
- `Shape` and topology-specific handles such as `Vertex`, `Edge`, `Wire`,
  `Face`, `Shell`, `Solid`, `Compound`, and `CompSolid`;
- `Curve2`, `Curve`, and `Surface`;
- `BoundaryBox` and typed domain sequences;
- mesh values if the vertical slice confirms that deferred mesh extraction is
  useful.

Known topology-producing operations return the most precise truthful handle.
Operations whose topology cannot be known before evaluation return `Shape`.
Resolution validates a declared result type.

`Scalar`, point, vector, transform, and geometry operations preserve the graph
when any input is deferred. Operations over entirely immediate inexpensive
values may be evaluated immediately without changing the result's public
type. Laziness and persistence are independent: a deferred value need not be
stored on disk.

The initial materialization boundaries are:

- Python control flow and comparisons returning `bool`;
- `float()`, `int()`, `len()`, and iteration where Python requires a concrete
  answer;
- conversion to NumPy or native OCP values;
- display, scene transport, export, and other I/O;
- foreign functions without a registered expression-aware adapter.

ZenCad may provide expression-aware numeric helpers such as `zencad.sin()` or
`zencad.sqrt()`. Passing a `Scalar` to an ordinary `math` function is allowed
to materialize it. Lazy `Boolean` and `Integer` types are not part of the
initial design.

Public handles use composition rather than inheriting from `float`,
`numpy.ndarray`, native OCP types, or evalcache expressions. Domain values are
logically immutable. Generic expression objects do not appear in the public
ZenCad API.

## ZenCad and evalcache boundary

Evalcache remains a separate generic computation engine. Its `v2` line will
provide:

- typed internal `Expression[T]` nodes and an evaluator;
- explicit evaluation and cache policies;
- deterministic hashing of registered operations and values;
- a cache-store protocol, null store, serializers, and file-artifact support;
- type-preserving argument resolution;
- progress and tree-inspection hooks;
- a temporary legacy `LazyObject` facade over the new kernel.

ZenCad owns domain handles, topology knowledge, OCP adapters and codecs,
product-level cache configuration, user settings, and materialization at
display/export/runtime boundaries. Evalcache does not know ZenCad settings,
OCP types, or the product's per-user default path.

Resolved cache values use registered codecs. The new expression and value
model receives a new cache namespace; existing cache entries are disposable
and will not be migrated.

## Compatibility policy

Some compatibility breaks are accepted. The migration should nevertheless
preserve common modelling syntax where that does not compromise the new type
model.

During a bounded transition:

- `.unlazy()` may materialize and return the same domain type;
- legacy native accessors such as `.Shape()` may remain explicit
  materialization boundaries;
- lowercase point/vector constructors may alias the new types;
- the old untyped `@lazy` API may remain under an explicitly legacy surface;
- a typed custom-operation API requires an explicit result type or return
  annotation.

The final distribution form is intentionally deferred. After the vertical
slice and migration cost are measured, the project will decide between an
incompatible new ZenCad major release and a separate `zencad2` repository.
That release decision must not distort the internal architecture meanwhile.

## Rationale

A generic `Lazy[T]` return type would improve static typing but would still
make users reason about evaluation state. Separate eager and lazy subclasses
would preserve the current dual model and keep `isinstance` and API signatures
policy-dependent. Typed handles preserve a normal domain API while retaining
deferred dependency graphs through geometry, points, vectors, sequences, and
scalars.

Keeping evalcache generic avoids duplicating graph evaluation, hashing, and
storage code inside ZenCad. Keeping domain handles in ZenCad prevents the
generic engine from acquiring OCP and product-policy dependencies.

## Alternatives considered

### Add annotations around the current proxy model

Rejected as the target architecture. It would publish temporary
`Shape | LazyObjectShape` and `Any`-like contracts and make the existing
manual proxy classification harder to remove.

### Expose a generic `Lazy[T]`

Rejected for the primary public API because evaluation state would remain a
user-visible concern. It may exist internally or in an advanced compatibility
API.

### Make shape handles typed but materialize points and scalars

Rejected because `shape.center()`, `mass()`, and `distance()` would
arbitrarily break dependency graphs and force expensive upstream geometry.

### Absorb evalcache into ZenCad immediately

Rejected. The expression evaluator and cache store remain a useful generic
boundary, and both repositories can be evolved together without introducing
ZenCad-specific policy into evalcache.

## Consequences and risks

- Error timing changes when an operation remains deferred longer than before.
- Small handles must be benchmarked to avoid unacceptable construction and
  memory overhead.
- Python `math`, NumPy, equality, hashing, collections, and OCP interop need
  explicit contracts.
- Deferred handles should remain unhashable until equality and hash semantics
  are proven coherent.
- OCP values are potentially mutable and must remain behind logically
  immutable resolved-domain adapters.
- User-defined lazy functions need a migration path based on declared result
  types.
- The new hash and codec contract invalidates the old cache namespace.
- Topology cannot always be predicted; the base `Shape` type remains necessary.

## Migration strategy

Implementation is gated and avoids a piecemeal public cutover:

1. Add characterization tests for current results, evaluation timing, cache
   reuse, errors, and common legacy calls.
2. Build the typed expression/evaluator and cache protocols in evalcache while
   retaining the legacy facade.
3. Build an internal ZenCad vertical slice covering primitive, transform,
   boolean, topology selection, point/scalar dependency, display, and export.
4. Stabilize scalar, point, vector, transform, topology, and typed-sequence
   algebra.
5. Migrate shapes, curves, surfaces, meshes, and runtime materialization
   boundaries behind the non-public typed layer.
6. Switch the public geometry API only after the coherent slice passes runtime,
   subprocess, cache, type-check, example, and performance gates.
7. Publish PEP 561 typing and later remove the bounded legacy facade.

The detailed live plan is maintained in
[`docs/development/typed-domain-migration.md`](../development/typed-domain-migration.md).

## Follow-up decisions

- Choose incompatible ZenCad major versus a separate `zencad2` repository
  after the vertical slice and compatibility audit.
- Decide the exact duration and removal release for `.unlazy()` and the legacy
  custom `@lazy` surface.
- Decide whether mesh values benefit enough from deferred handles to join the
  initial public domain.

