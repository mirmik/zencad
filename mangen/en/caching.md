# Evaluation and caching

Evaluation is deferred by default: operations construct a graph, and geometry is computed for display, export, `native()` or `value()`. Caching reuses identical computation results, including across processes.

Enable immediate evaluation before constructing your model when debugging:

```python
import zencad as z

z.configure(cache_enabled=False)
z.set_evaluation_mode("immediate")
body = z.box(20) - z.cylinder(3, 20)
assert isinstance(body, z.Shape)
z.set_evaluation_mode("deferred")
```

The mode persists until changed and does not alter object types. Switching does not evaluate all existing expressions. Caching is independent: disabling it does not disable lazy evaluation.

| Mode | `cache_enabled=False` | `cache_enabled=True` |
| --- | --- | --- |
| `immediate` | The operation runs immediately without reading or writing the disk cache. | The result is requested immediately: loaded from disk cache, or computed and stored on a miss. |
| `deferred` | The operation runs when its result is needed, without reading or writing the disk cache. | When needed, the result is loaded from disk cache, or computed and stored on a miss. |

`configure(cache_enabled=False)` disables disk cache reads and writes without deleting its files. Objects can reuse already computed results in memory. The table describes cacheable operations; simple values may be evaluated while constructing the graph.

## Shared disk cache

The default directory is `tempfile.gettempdir()/zencad-cache-<uid>`. ZenCad does not delete it on exit, but the OS may clean temporary storage. Precedence is explicit process `configure()`, then `ZENCAD_CACHE_DIR`/`ZENCAD_CACHE_DISABLE`, then saved user settings.

```python
import zencad as z

z.configure(cache_dir="./model-cache", cache_enabled=True)
body = z.box(5)
print(body.mass().value())
```

`ZENCAD_CACHE_DISABLE=1` disables disk cache reads and writes. `z.clear_cache()` explicitly clears the configured cache; ordinary scripts do not need to call it.

## Diagnostics without the editor

```sh
zencad inspect model.py --eager --no-cache --json
zencad inspect model.py --tree
zencad inspect model.py --tree --failed-path
```

A script header can override the runner's initial mode. The graph exposes dependencies, cache hits and failures. [Command line](headless.html).

Integrations can use an explicit owner: `context = z.Context.deferred(cache=False)` and `context.call(z.box, 10)`. `Context` has no CAD facade; ordinary scripts do not need one. Old `zencad.lazy` settings appear only in the [migration guide](migration.html).
