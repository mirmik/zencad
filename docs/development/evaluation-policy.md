# Evaluation policy

ZenCad uses one evaluation mode for a script. Select it before execution through
CLI/Python runner options, or set it in the script header:

```python
import zencad

zencad.configure(cache_enabled=False)  # optional, independent cache setting
zencad.set_evaluation_mode("immediate")
model = zencad.box(20) - zencad.cylinder(3, 20)
```

The default is `"deferred"`. The other mode, `"immediate"`, evaluates each
operation when it is constructed, so geometry failures are reported at the
operation instead of a later display, export, `native()`, or `value()` call.
Both modes return the same public domain types.

`set_evaluation_mode` accepts a string or `EvaluationMode` and returns `None`.
`evaluation_mode()` reports the selected mode. The setting persists until
explicitly changed; it is not a context manager. Set it before constructing the
model. Changing it updates the existing evaluator without changing handle
ownership or discarding cached values, progress hooks, or graph recording.
Already-created expressions are evaluated when needed, not by the setter itself.
Subsequent cache configuration does not reset the selected default mode.

```sh
zencad inspect model.py --evaluation immediate --no-cache --json
# Equivalent short spelling:
zencad inspect model.py --eager --no-cache --json
```

The isolated runner receives the initial mode and cache policy as data. Python
runner APIs accept `evaluation_mode="immediate"` and `cache_enabled=False`.
A mode explicitly set in the script header overrides that initial mode inside
the child process, without changing the parent process. Cache remains controlled
independently through the runner options or `zencad.configure`.

The former public `eager()`, `immediate()`, `deferred()`, and `evaluation()`
context managers are removed. ZenCad 1 scripts using `zencad.lazy.onplace = True`
should use `zencad.set_evaluation_mode("immediate")` in the script header.
Explicit low-level `Context` ownership remains available to internal integrations;
script authors do not need to create or nest contexts to select evaluation timing.
