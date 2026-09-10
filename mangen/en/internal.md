# ZenCad internals

## Geometry kernel and evaluation

ZenCad uses OpenCascade through `cadquery-ocp-novtk` and its `OCP` Python modules. ZenCad geometry types and operations live in `zencad.geom`; kernel adapters live in `zencad._native`.

Geometry objects and values retain dependencies between operations. The EvalCache evaluator executes them in `deferred` or `immediate` mode and manages result reuse. A `Context` owns an evaluator; ordinary scripts use module functions and object methods. `.value()` obtains a computed value, while a shape's `.native()` obtains an OCP object. See [Evaluation and caching](caching.html) and [Values, points and transforms](prim0d.html).

## Organization and interaction of ZenCad threads and processes.

The ZenCad graphical interface is designed to minimize its influence on the order of calculations in the running scripts. To achieve this, scripts run in a separate process.

When started with `zencad model.py` or `python -m zencad model.py`, the main process owns Qt, the OpenCascade viewer and the OpenGL context. Camera, selection, markers and AIS presentation objects also belong to this process.

`RunnerSupervisor` starts a separate model process using the `multiprocessing` `spawn` method. The runner constructs geometry and collects the scene without creating Qt or OpenGL windows. Scene data crosses the process boundary: serialized BREP geometry or meshes, placements, colors, names and visibility. The viewer window belongs to the main process and persists across model evaluations.

Communication uses `multiprocessing.Pipe` connections and a versioned protocol. Messages carry scene snapshots, evaluation progress, script output and errors; control events and user input travel in the opposite direction. The runner captures script stdout and stderr and delivers them to the interface as messages.

## Evaluation and scene updates

Each run receives a generation number. The runner collects object descriptions in a `SceneDraft` and publishes a `SceneSnapshot`. The GUI's `ScenePresenter` validates and decodes the snapshot before replacing the viewer contents. Only the current generation can be applied: a late message from a previous run cannot replace the current model.

The last successful scene remains visible during evaluation, cancellation or failure. Camera state is preserved by default. A runner can be stopped and replaced without recreating the main window or viewer.

## What show() does

Its behavior depends on how the script is launched:

- In scripts launched by the editor or `inspect`/`check`, `display()` adds data to a `SceneDraft`, and `show()` publishes a snapshot. Static scripts then continue without entering a GUI event loop.
- In a direct `python model.py` run, `show()` opens a standalone viewer in the same process and starts the Qt event loop. It does not create the full editor. This mode is also available through `zencad --display model.py`.
- `zencad --no-show model.py` executes a script with display disabled. Use [inspect and check](headless.html) to obtain geometry reports.

## Animation and input

In the editor, an animated runner stays active after publishing the scene. Its callback receives timing, input through `state.input` and camera controls through `state.camera`. Placement, color and visibility changes are sent as scene updates; camera actions use separate messages. Qt event handling and presentation run in the GUI process.

Construct geometry for managed animations before the initial `show()`. The callback has no direct viewer-widget access and cannot replace geometry after publication. See [Animation](animate.html) for the contract and examples.

See [Runtime architecture](../development/runtime-architecture.md) for protocol details, object ownership and lifecycle.
