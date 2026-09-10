# Evaluation and caching

Scripted CAD needs to rerun the geometry script whenever the model changes. As a model grows, calculating and displaying it takes longer. ZenCad uses [evalcache](https://github.com/mirmik/evalcache) to cache expensive operations and evaluate them lazily.

Instead of calculating immediately, evalcache builds a model construction tree from the objects' hash keys. It saves cacheable results on disk and retrieves them when the same object has already been calculated. Changing parameters on the next run changes the keys of dependent computations.

Evaluation is deferred by default (`deferred`): operations create a graph, and geometry is computed when needed for display, export, `native()` or `value()`. The cache reuses identical results, including in a new process.

### Debugging lazy evaluation

Because evalcache computes an object when it is requested rather than when it is declared, the origin of an error can be harder to locate. Some operations also trigger implicit evaluation of lazy objects.

For debugging, enable immediate evaluation at the top of the script. Public object types stay the same:

```python
import zencad as z

z.configure(cache_enabled=False)
z.set_evaluation_mode("immediate")
body = z.box(20) - z.cylinder(3, 20)
assert isinstance(body, z.Shape)
z.set_evaluation_mode("deferred")
```

The mode stays in effect until changed and does not alter object types. Switching modes does not evaluate all existing expressions. The cache is independent: disabling it does not itself disable lazy evaluation.

| Mode | `cache_enabled=False` | `cache_enabled=True` |
| --- | --- | --- |
| `immediate` | The operation runs immediately, without reading or writing the disk cache. | The result is requested immediately: read from the cache, or computed and saved on a miss. |
| `deferred` | The operation runs when its result is needed, without reading or writing the disk cache. | When needed, the result is read from the cache, or computed and saved on a miss. |

`configure(cache_enabled=False)` disables disk cache reads and writes without deleting its files. Objects may reuse results already computed in memory. The table describes cacheable operations; simple values may be evaluated while the graph is built.

## Shared disk cache

By default, all ZenCad processes for the current user share `tempfile.gettempdir()/zencad-cache-<uid>`. ZenCad does not delete it on exit, but the operating system may clear temporary storage.

The cache directory and enabled state can be changed in ZenCad's settings. Precedence is explicit process `configure()`, then `ZENCAD_CACHE_DIR`/`ZENCAD_CACHE_DISABLE`, then saved user settings.

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

A script header can override the runner's initial mode. The graph shows dependencies, cache hits and errors. [Command line](headless.html).

Integrations can use an explicit computation owner: `context = z.Context.deferred(cache=False)` and `context.call(z.box, 10)`. `Context` has no CAD facade; ordinary scripts do not need a separate context. Old `zencad.lazy` settings are described in the [migration guide](migration.html).
