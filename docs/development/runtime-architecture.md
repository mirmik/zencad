# Planned runtime architecture

> Status: migration in progress.  The transport protocol and runner-side
> `SceneDraft` path are implemented; the persistent presenter and supervisor
> are not yet the default execution path.  The accepted decision is recorded in
> [Persistent viewer and scene snapshots](../architecture-council/2026-08-01-persistent-viewer-scene-snapshots.md).

ZenCad is migrating from cross-process native-window embedding to a persistent
viewer fed by versioned scene snapshots.

## Process ownership

### GUI process

The long-lived GUI process owns all presentation and interaction state:

- `QApplication`, editor widgets, and the main window;
- the single native viewer window and OpenGL context;
- `V3d_Viewer`, `V3d_View`, and `AIS_InteractiveContext`;
- AIS objects, selection, camera, markers, and navigation state;
- scene commit, redraw, and user-facing diagnostics;
- runner lifecycle and generation selection.

Qt, AIS, and native-window objects must not cross the process boundary.

### Runner process

A runner evaluates a user script in isolation and owns only computation-side
state:

- the script namespace, imports, working-directory contract, and EvalCache;
- lazy evaluation and `TopoDS_Shape` construction;
- a data-only scene draft created by `display()`;
- BREP serialization and snapshot publication;
- progress, stdout/stderr, and structured error reporting.

A runner must not import or initialize the ZenCad GUI stack.  It is disposable:
a superseded, crashed, or unresponsive runner can be replaced without
restarting the GUI.

## Snapshot lifecycle

```text
open/reload script
      |
      v
RunnerSupervisor assigns generation N
      |
      v
runner evaluates -> SceneDraft -> immutable SceneSnapshot
      |
      v
GUI validates generation and fully decodes snapshot
      |
      v
ScenePresenter atomically replaces AIS contents
      |
      v
single viewer update; camera preserved by default
```

Only the newest generation may commit.  The last successful snapshot remains
presented during calculation, cancellation, and failure.

## Protocol boundary

The control protocol is versioned and framed.  It needs at least these message
classes:

- `run`: script path, generation, arguments, settings, and environment policy;
- `cancel`: generation and reason;
- `progress`: generation and structured evaluation progress;
- `output`: generation, stream, and text chunk;
- `scene`: manifest plus binary payloads;
- `error`: generation, exception summary, and traceback;
- `finished`: generation and terminal status.

The first scene manifest should describe a full replacement, not a diff.  Each
object needs an ID, kind, payload reference, transform, visibility, and style.
Shape payloads use BREP bytes.  The transport spike must choose between direct
binary pipe frames and file-backed blobs using measured scene sizes; the
logical manifest must not depend on that choice.

The transport spike selected inline binary frames through 32 MiB and atomic
file-backed bundles above that boundary.  The format, benchmark, and integrity
rules are recorded in [SceneSnapshot transport v1](scene-snapshot-transport.md).

Python pickle is not the protocol.

## Transactional presentation

`ScenePresenter` receives a fully validated decoded snapshot.  On the GUI
thread it:

1. materializes all supported AIS objects;
2. prepares the new presentation without redrawing;
3. removes presentation objects belonging to the previous snapshot;
4. displays the new set with viewer updates disabled;
5. applies the requested camera policy;
6. performs one viewer update and records the committed generation.

If validation, decoding, or materialization fails before commit, the previous
scene remains active and the failure is reported.  Scene-owned AIS objects
must be tracked separately from permanent viewer helpers such as axes and
markers; a scene replacement must not call an indiscriminate `RemoveAll()`.

## API transition

The current `Scene` mixes scene description with eagerly created AIS objects.
The planned split is:

- runner-side `SceneDraft` and logical object references;
- immutable `SceneSnapshot` data transfer objects;
- GUI-side `ScenePresenter` and presentation handles.

Under a managed runner, `display()` adds a description to the current draft
and returns a logical object reference.  Mutations before `show()` update that
description.  `show()` publishes the immutable snapshot and does not start a
second Qt event loop.

The first managed adapter is the explicit `managed_scene(generation,
publisher)` context.  Inside it, the regular public `display()` and `show()`
functions target a data-only `SceneDraft`; `show()` invokes the publisher and
returns the same snapshot without importing Qt or entering ZenFrame.  Shape
references currently preserve transform, visibility, face color, border
color, and wire color.  Unsupported presentation kinds fail explicitly until
their snapshot representation is added.

Standalone and headless modes need explicit adapters; they must not infer
process role by importing Qt.  Existing animation and post-`show()` object
mutation are outside the first static-snapshot milestone and require a
follow-up live-update protocol.

## Cancellation and failure

Cancellation is generation-based.  The supervisor first requests cooperative
cancellation so EvalCache and controlled algorithms can stop cleanly.  After
a bounded grace period it terminates the runner.  Any later messages from that
generation are ignored.

Runner failure never clears the committed scene.  Protocol corruption or an
unsupported object kind is a failed generation with an actionable diagnostic,
not a partial scene.

## Migration boundary

The first integration may continue using ZenFrame editor widgets, but must
bypass its unbound worker and foreign-window embedding path.  Legacy
`bindwin`, `QWindow.fromWinId()`, and `createWindowContainer()` code can be
removed only after static scenes, errors, reload, cancellation, camera
preservation, and supported interactive objects pass the replacement-path
smokes.
