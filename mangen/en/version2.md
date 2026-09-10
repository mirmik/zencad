# How ZenCad 2 differs from ZenCad 1

ZenCad 2 retains Python scripting for modeling, while changing geometry-backend installation, viewer architecture and the representation of computation results. These changes simplify installation, separate model evaluation from presentation and make the API more predictable for people and software tools.

## Geometry kernel and installation from PyPI

The geometry kernel itself remains **OpenCascade**. Its Python bindings change from `pythonocc-core` to `cadquery-ocp-novtk`, exposed through the `OCP` modules.

In ZenCad 1, geometry dependencies required separate attention to the distribution of `pythonocc-core` and OpenCascade. In ZenCad 2, the backend is distributed as prebuilt binary wheels through PyPI and installed as a ZenCad dependency. Supported platforms do not require a separate OpenCascade build or a Conda environment.

```sh
python3 -m pip install "zencad[gui]"
```

This installs the published package. If the desired ZenCad 2 revision has not been published yet, install from source. See [Installation](installation.html) for installation options and platform requirements.

## A persistent viewer instead of embedded windows

In ZenCad 1, the model process created its own viewer window, which was embedded in the application's main window. Re-evaluating a model affected both computation and the lifecycle of that window. This design depended on window-system mechanisms.

In the ZenCad 2 editor, the viewer belongs to the main GUI process and persists across script runs. Qt, OpenGL, the camera and OpenCascade presentation objects live in that process. A separate model runner computes geometry without creating a window to embed.

| ZenCad 1 | ZenCad 2 |
| --- | --- |
| The model process creates a viewer window. | The model process collects scene data. |
| The main window embeds another process's window. | The main window displays data in its own persistent viewer. |
| Restarting computation involves replacing the model window. | The runner restarts; the viewer and camera persist. |

When running `python model.py` directly, `show()` opens a standalone viewer in the script process. The GUI/runner separation described here applies to the editor.

## How geometry crosses process boundaries

The runner collects a scene description: shapes, placements, colors, visibility and names. BREP geometry is serialized to bytes; meshes are transmitted as vertex and triangle data. Together with presentation properties, these form a `SceneSnapshot` sent through the interprocess protocol.

The GUI decodes the snapshot and creates its own AIS presentation objects. The process boundary carries **geometry data**, not a window, OpenCascade object pointers or Qt objects.

Each run has a generation number. The GUI accepts the current run's result; a late result from an earlier evaluation cannot replace the current scene. The last successful result remains visible during computation or on failure. Animations send placement, color and visibility updates without retransmitting all geometry on each frame.

The same scene representation supports automated analysis: `inspect` and `check` can obtain a model's result without starting a viewer. See [ZenCad internals](internal.html) and [Working with an agent](agents.html).

## Object types and lazy evaluation

In ZenCad 1, laziness was visible in result types: deferred operations could return `LazyObject` and `LazyObjectShape` wrappers. `Shape` was the main representation of topology objects; `point3` and `vector3` were classes derived from NumPy arrays.

In ZenCad 2, public objects retain their types regardless of evaluation mode. Solids, faces, edges and vertices use types such as `Solid`, `Face`, `Edge` and `Vertex`; numbers, points and vectors use `Scalar`, `Point3`, `Vector3` and other value types. Objects retain their lazy graphs internally. Switching between `deferred` and `immediate`, or enabling caching, does not replace their classes.

Scripts construct values with lowercase functions:

```python
from zencad import *

p = point3(1, 2, 3)
v = vector3(4, 0, 0)
body = box(10)
volume = body.mass()

assert isinstance(p, Point3)
assert isinstance(body, Solid)
assert isinstance(volume, Scalar)
assert (p + v).value() == (5, 2, 3)
assert abs(float(volume) - 1000) < 1e-7
```

`point3` is now a function constructing a `Point3`, rather than the class itself. Points and vectors are not NumPy arrays; use `.to_numpy()` to obtain an array. Request numeric values with `.value()` or `float()`, and an OCP shape with `.native()`.

Topology queries return `ShapeList` collections with specific element types. For example, `body.faces()` contains `Face` objects, while `body.vertices()` contains `Vertex` objects; use `.point()` to obtain vertex coordinates. Indexing and selectors retain dependencies, while iteration and collection length require evaluation.

## Lazy evaluation: EvalCache v2

ZenCad 1 used `Lazy` and generic `LazyObject` wrappers. Evaluation and caching were configured through `zencad.lazy`, and user functions could be wrapped with `@lazy`.

ZenCad 2 uses the **EvalCache v2** evaluator. Operations form a graph with explicitly declared result types and serialization rules. Public geometry objects contain either a value or an expression in that graph. Evaluation remains lazy, but users work with `Solid`, `Point3` or `Scalar` objects instead of generic wrappers.

Dependencies can also pass through numeric results. For example, one shape's volume can participate in another operation without first converting it to a Python number:

```python
from zencad import *

body = box(10)
volume = body.mass()
moved = body.right(volume / 100)
assert abs(float(moved.center().x) - 15) < 1e-7
```

`volume / 100` retains the graph dependency; an explicit `float()` requests the computed number. The graph also supports diagnostics: `inspect --tree` shows operations and dependencies, while `--failed-path` helps trace a failed computation.

Execution mode and caching are configured independently:

- `set_evaluation_mode("deferred")` delays evaluation until a result is requested; `set_evaluation_mode("immediate")` evaluates operations as they are constructed.
- `configure(cache_enabled=True)` enables disk caching; `False` disables cache reads and writes without disabling the dependency graph.

The combinations are shown in the table in [Evaluation and caching](caching.html). ZenCad 1 cache files are not a compatible cache for ZenCad 2.

The old `zencad.lazy` object and `@lazy` decorator are not supported. Call replacements and script adaptation rules are described separately in [Migrating from ZenCad 1](migration.html).
