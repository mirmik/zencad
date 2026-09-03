# Headless model inspection

`zencad inspect` evaluates a model in the managed, isolated script runner and
describes its final static scene without constructing a Qt application, AIS
presentation, OpenGL context, or editor window. It is intended for agents, CI
checks, and shell pipelines that need geometry facts rather than a screenshot.

```sh
zencad inspect model.py --json
zencad inspect model.py --output report.json
zencad inspect model.py --timeout 10 --json -- model-argument
zencad inspect model.py --eager --no-cache --json
zencad inspect model.py --tree
zencad inspect model.py --graph-json computation.json
```

`--json` writes exactly one JSON document to stdout. Output produced by the
model is forwarded to stderr. `--output` atomically replaces its destination;
it can be combined with `--json`. Without either option, the command prints a
short human-readable summary.

Evaluation is deferred by default. `--evaluation immediate` or its `--eager`
shortcut evaluates every model operation as it is constructed, which usually
places geometry failures closer to their source line. `--no-cache`
independently disables cache reads and writes for that run. The corresponding
Python keyword arguments are `evaluation_mode="immediate"` and
`cache_enabled=False`.

## Computation graph

`--tree` prints the EvalCache computation graph rooted at displayed scene
objects. A shared expression is expanded once and then marked `(shared)`, so
the output describes a DAG rather than duplicating work. Each line includes
the canonical operation ID, evaluation state, cache hit/miss state, optional
duration, and the stable expression digest prefix.

`--graph-json PATH` writes the complete versioned graph (`schema:
"zencad.computation_graph"`, version 1) while the ordinary inspection result
continues to stdout. It can be combined with `--tree`. The graph contains
stable full-digest node IDs, ordered dependency IDs, short argument summaries,
result type IDs, source file/line when available, and evaluation errors. It
never contains BREP/mesh payloads, arbitrary object reprs, or memory addresses.

Graph capture is bounded to 4096 nodes by default. `--max-graph-nodes N`
changes that bound and the JSON `limits.truncated` flag reports an incomplete
capture. Views can be narrowed with repeatable `--root object-000000`,
`--max-depth N`, `--failed-path`, and `--hide-literals`. `--failed-path` is
especially useful when script evaluation fails: the partial DAG is emitted
before the usual exit code 3.

The typed, Qt-free API returns the same contract:

```python
from zencad import inspect_computation_graph

graph = inspect_computation_graph("model.py", max_nodes=2000)
print(graph.to_tree())
for node in graph.nodes:
    print(node.operation, node.dependencies, node.cache)
```

The same operation is available as a Qt-free Python API:

```python
from zencad import inspect_script

report = inspect_script("model.py", timeout=10)
for item in report.objects:
    print(item.object_id, item.kind, item.geometry["bbox"])
```

## JSON contract

Successful reports use `schema: "zencad.inspect"` and `schema_version: 1`.
Consumers must check both fields before interpreting the rest of the document.
Top-level fields are:

- `status`: `"ok"` for a complete report;
- `script.path`: the absolute model path, or `null` for snapshots inspected
  directly through `inspect_snapshot`;
- `scene`: object counts and scene metadata;
- `objects`: scene order, with stable `id`, optional `name`, `kind`, `visible`,
  `presentation`, and `geometry` fields.

All object kinds include a SHA-256 digest of their transported geometry and a
world-space bounding box. BRep objects additionally include shape type,
surface area and center, volume and center where applicable, unique topology
counts, and the complete versioned validation report. Mesh objects include
vertex and triangle counts, surface area, and a degenerate-triangle count.
Points include world coordinates; lines include world endpoints and length.

An invalid but decodable shape remains part of a successful inspection and has
`geometry.valid: false` with details in `geometry.validation`. This is
deliberate: inspection reports facts. Use `zencad check model.py --valid` when
invalid geometry should fail a build; its contract is documented in
[`headless-check.md`](headless-check.md).

Terminal failures still produce the same schema when `--json` or `--output` is
used, with `status: "error"` and a structured `error` object. Script tracebacks
are data inside that JSON document, never loose text on stdout.

## Exit codes

| Code | Meaning |
| ---: | --- |
| 0 | Inspection completed, including inspectable invalid geometry |
| 2 | Invalid command-line usage |
| 3 | Script failure or unsupported animated scene |
| 4 | Missing scene or geometry that could not be decoded/measured |
| 5 | Script evaluation timed out |
| 6 | The requested report file could not be written |

The bundled `zencad/examples/0.Base/agent_inspection.py` is a small inspection
target. For example:

```sh
zencad inspect zencad/examples/0.Base/agent_inspection.py --json
```
