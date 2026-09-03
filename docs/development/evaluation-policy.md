# Evaluation policy

ZenCad operations always return the same public domain handles (`Solid`,
`Face`, `Curve`, `Scalar`, and so on). Evaluation timing and cache access are
independent policies owned by a `Context`; neither policy changes those public
classes.

The default is deferred evaluation with the configured shared cache. For a
scoped immediate run use `eager` (an alias for `immediate`):

```python
import zencad

with zencad.eager(cache=False) as context:
    model = zencad.box(20) - zencad.cylinder(3, 20)
    assert model.context is context
```

Every expression is evaluated when it is constructed, so geometry failures
are reported at the declaring operation instead of a later `display`, export,
`native`, or `value` boundary. Evaluated handles still retain their expression
identity where required for deterministic DAG and cache semantics.

The complete public context-manager API is:

```python
with zencad.evaluation("immediate", cache=True):
    ...

with zencad.immediate():
    ...

with zencad.eager():
    ...

with zencad.deferred(cache=False):
    ...

mode = zencad.evaluation_mode()  # EvaluationMode.DEFERRED or IMMEDIATE
```

`cache=None` (the default) inherits the outer context's cache policy and store.
`cache=False` disables reads and writes in the scoped context. Nested policy
blocks restore the exact outer context even when an exception leaves the inner
block. Handles belong to the context that created them and must not be mixed
across policy blocks.

For lower-level ownership, the equivalent explicit API remains available:

```python
context = zencad.Context.immediate(cache=False)
shape = context.call(zencad.box, 10)
```

Headless model inspection accepts the same independent choices:

```sh
zencad inspect model.py --evaluation immediate --no-cache --json
# Short spelling:
zencad inspect model.py --eager --no-cache --json
```

The isolated runner receives both policies as data. It does not mutate the
parent process's context, import Qt, or rely on the removed
`zencad.lazy.onplace` global. Existing ZenCad 1 code that used
`zencad.lazy.onplace = True` should place the relevant model construction in a
`with zencad.eager():` block instead.
