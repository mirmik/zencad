:ru
# Вычисления и кэш

По умолчанию вычисления отложены (`deferred`): операции создают граф, а геометрия вычисляется, когда нужна для отображения, экспорта, `native()` или `value()`. Кэш помогает повторно использовать результаты одинаковых вычислений, в том числе в новом процессе.

Для отладки включите немедленные вычисления до построения модели:

```python
import zencad as z

z.configure(cache_enabled=False)
z.set_evaluation_mode("immediate")
body = z.box(20) - z.cylinder(3, 20)
assert isinstance(body, z.Shape)
z.set_evaluation_mode("deferred")
```

Режим действует до явного изменения и не меняет типы объектов. Переключение не вычисляет все уже созданные выражения. Кэш независим от режима: его отключение само по себе не отключает ленивые вычисления.

| Режим | `cache_enabled=False` | `cache_enabled=True` |
| --- | --- | --- |
| `immediate` | Операция вычисляется сразу, без чтения и записи дискового кэша. | Результат запрашивается сразу: берётся из дискового кэша, а при отсутствии вычисляется и сохраняется. |
| `deferred` | Операция вычисляется, когда нужен результат, без чтения и записи дискового кэша. | Когда результат понадобится, он берётся из дискового кэша, а при отсутствии вычисляется и сохраняется. |

`configure(cache_enabled=False)` отключает чтение и запись дискового кэша, но не удаляет его файлы. Уже вычисленные результаты объектов могут повторно использоваться в памяти. Таблица описывает операции, допускающие кэширование; простые значения могут вычисляться при построении графа.

## Общий дисковый кэш

По умолчанию каталог: `tempfile.gettempdir()/zencad-cache-<uid>`. ZenCad не удаляет его при выходе, но временный каталог может очистить ОС. Приоритет настроек: явный `configure()` в процессе, затем `ZENCAD_CACHE_DIR`/`ZENCAD_CACHE_DISABLE`, затем сохранённые пользовательские настройки.

```python
import zencad as z

z.configure(cache_dir="./model-cache", cache_enabled=True)
body = z.box(5)
print(body.mass().value())
```

`ZENCAD_CACHE_DISABLE=1` отключает чтение и запись дискового кэша. `z.clear_cache()` явно очищает настроенный кэш; в обычном скрипте вызывать его не требуется.

## Диагностика без редактора

```sh
zencad inspect model.py --eager --no-cache --json
zencad inspect model.py --tree
zencad inspect model.py --tree --failed-path
```

Заголовок скрипта может переопределить начальный режим runner. Граф показывает зависимости, cache hit и ошибки. [Командная строка](headless.html).

Для интеграций доступен явный владелец вычислений: `context = z.Context.deferred(cache=False)` и `context.call(z.box, 10)`. У `Context` нет CAD-фасада; для обычных скриптов отдельный контекст не нужен. Старые настройки `zencad.lazy` описаны только в [руководстве миграции](migration.html).
:en
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
::
