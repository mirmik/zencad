# ZenCad internals

## Geometry kernel and evaluation

ZenCad uses the OpenCascade geometry kernel. The `cadquery-ocp-novtk` package provides Python access through the `OCP` modules. ZenCad's geometric types and operations live in `zencad.geom`; kernel adapters live in `zencad._native`.

Geometry objects and values preserve operation dependencies. EvalCache evaluates them in `deferred` or `immediate` mode and manages result reuse. `Context` owns the evaluator; ordinary scripts can use module functions and object methods. `.value()` obtains a computed value; `.native()` on a shape returns an OCP object. See [Evaluation and caching](caching.html) and [Points and vectors](prim0d.html).

## Threads, processes and communication

ZenCad's graphical interface is designed to interfere as little as possible with script execution. Scripts therefore run in a separate process.

When launched with `zencad model.py` or `python -m zencad model.py`, the main process owns the Qt interface, OpenCascade viewer and OpenGL context. It also owns the camera, selection, markers and AIS display objects.

`RunnerSupervisor` starts a model worker with `multiprocessing` using `spawn`. The worker builds geometry and assembles the scene without creating Qt or OpenGL windows. Processes exchange scene data: serialized BREP geometry or meshes, placements, colors, names and visibility. The viewer window belongs to the main process and survives model recomputation.

Communication uses `multiprocessing.Pipe` channels and a versioned protocol. Scene snapshots, progress, script output and errors travel to the GUI; control events and user input travel back. The worker captures script `stdout` and `stderr` and delivers them as messages.

## Recomputing and updating the scene

Each run receives a generation number. The worker gathers object descriptions in `SceneDraft`; publishing produces a `SceneSnapshot`. The GUI's `ScenePresenter` validates and decodes it, then replaces the viewer contents. Only the current generation is applied: a late message from an earlier run cannot replace the current model.

The last successful scene remains visible during calculation, cancellation or an error. Camera placement is preserved by default. The worker can be stopped and restarted without recreating the main window or viewer.

## The show function

The behavior of `show` depends on context (see `zencad/showapi.py`).

- In a script run by the editor or by `inspect`/`check`, `display()` adds data to `SceneDraft`, and `show()` publishes a scene snapshot. For a static scene, execution then continues without starting a window event loop.
- Running `python model.py` directly makes `show()` open a standalone viewer in the same process and start the Qt event loop. It does not create the full editor. This mode is also available through `zencad --display model.py`.
- `zencad --no-show model.py` executes a script with display disabled. Use the separate [inspect and check](headless.html) commands for geometry reports.

## Animation and input

In the editor, an animated worker stays active after publishing its scene. The callback receives timing, input through `state.input` and camera controls through `state.camera`. Placement, color and visibility changes are sent as scene updates; camera actions use separate messages. Qt events and rendering are handled in the GUI process.

Create animation geometry before the initial `show()`. The callback does not directly access the viewer widget or replace geometry after publication. See [Animation](animate.html) for the contract and examples.

Protocol, ownership and lifecycle details: [Runtime architecture](../development/runtime-architecture.md).
