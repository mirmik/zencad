# Runtime architecture

> Status: implemented. The transport protocol, runner-side `SceneDraft`,
> persistent `ScenePresenter`, generation supervisor, managed animations, and
> typed input are the only editor runtime. The former cross-process native
> window path has been removed. The accepted decision is recorded in
> [Persistent viewer and scene snapshots](../architecture-council/2026-08-01-persistent-viewer-scene-snapshots.md).

ZenCad uses one persistent viewer fed by versioned scene snapshots from
isolated script runners.

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

## Cache configuration

ZenCad uses one disk cache shared by all processes of the current
operating-system user. The path and enabled state live in the Qt-independent
user settings. By default the path is
tempfile.gettempdir()/zencad-cache-<uid>; ZenCad does not remove it on process
exit.

The effective configuration is selected in this order:

1. the current process's explicit zencad.configure(...) call;
2. ZENCAD_CACHE_DIR and ZENCAD_CACHE_DISABLE;
3. cache.directory and cache.enabled in user settings.

RunnerSupervisor sends the resolved directory and enabled state to each
runner before evaluating the user script. Disabling cache reads and writes
does not disable lazy evaluation. The accepted rationale and security boundary
are recorded in
[Shared user cache and Qt-independent configuration](../architecture-council/2026-08-30-shared-user-cache.md).

## Computation model

The runner evaluates the same public domain handles exported by `zencad`. A
minimal `Context` owns one EvalCache v2 evaluator, cache policy, store, and
progress hooks. It does not expose CAD methods: scripts use module operations,
domain methods, or `context.call(zencad.box, ...)` when they need an explicit
owner. Deferred/immediate and cache on/off policies never change public classes.

The scoped public spelling is `with zencad.eager(cache=False):`; the symmetric
`evaluation(...)`, `immediate()`, and `deferred()` context managers restore the
outer context on exit. Headless inspection passes the same policy through the
runner protocol with `--eager`/`--evaluation` and `--no-cache`. The full
contract is documented in [`evaluation-policy.md`](evaluation-policy.md).

`zencad inspect` materializes a versioned geometric report from the final
snapshot. `zencad check` applies typed expectations to that same report and
uses a distinct exit code for assertion failures, without conflating them with
script, geometry, or timeout errors. The check schema and aggregation rules are
documented in [`headless-check.md`](headless-check.md).

`Shape`, its exact topology subtypes, values, curves, surfaces, transforms,
bounds, meshes, and structured results retain expressions internally. The
runner reports v2 evaluation events directly; it does not install the former
LazyObject notification bridge. The old `Runtime` facade,
`RuntimeCompatibility`, `zencad.lazy`, `LazyObjectShape`,
`.unlazy()`, and `zencad/lazifier.py` are removed.

Materialization is explicit and directional:

- `value()` returns an immutable Python record or scalar snapshot;
- `native()` returns an owned mutable OCP snapshot;
- scene/export boundaries encode BREP or mesh data and do not leak native OCP
  ownership across processes;
- canonical domain types and operations live in `zencad.geom`;
- private eager `zencad._native` adapters operate only at explicit OCP
  boundaries and do not construct evaluation proxies.

Topology queries return `ShapeList[T]` with precise element types. Indexing,
filtering, sorting, and domain composition retain graph ownership; iteration,
length, `value()`, `native()`, and transport encoding are deliberate
evaluation boundaries. Selector identity and tolerance semantics are detailed
in [`topology-selectors.md`](topology-selectors.md).

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

The control protocol is versioned and framed. It contains these message
classes:

- `run`: script path, generation, arguments, settings, and environment policy;
- `cancel`: generation and reason;
- `progress`: generation and structured evaluation progress;
- `output`: generation, stream, and text chunk;
- `scene`: manifest plus binary payloads;
- `ready`: initial scene revision and static/animated lifecycle mode;
- `scene_patch`: versioned absolute live property updates;
- `error`: generation, exception summary, and traceback;
- `finished`: generation and terminal status.

The first scene manifest describes a full replacement, not a diff. Each
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

The implemented `ScenePresenter` belongs to one `DisplayWidget` and reuses its
native window, `V3d_View`, and `AIS_InteractiveContext` for every generation.
It materializes and validates all records before touching the context, removes
and displays only its own AIS handles with viewer updates disabled, clears
selection on every successful full replacement, and performs one final viewer
update.  A failed validation preserves both selection and the last scene; a
mid-commit failure rolls back the previous scene and camera.  `preserve` fits
the first successful scene and keeps the camera thereafter, while `fit` and
an explicit camera in snapshot metadata are opt-in policies.

## API transition

Legacy direct display still has a `Scene`, while the editor runtime uses this
implemented split:

- runner-side `SceneDraft` and logical object references;
- immutable `SceneSnapshot` data transfer objects;
- GUI-side `ScenePresenter` and presentation handles.

Under a managed runner, `display()` adds a description to the current draft
and returns a logical object reference.  Mutations before `show()` update that
description.  `show()` publishes the immutable snapshot and does not start a
second Qt event loop.

The first managed adapter is the explicit `managed_scene(generation,
publisher)` context.  Inside it, the regular public `display()` and `show()`
functions target a data-only `SceneDraft`.  Static `show()` invokes the
snapshot and ready publishers and returns the same snapshot without importing
Qt or entering the GUI application.  Animated `show()` keeps the runner alive, calls the
user callback at `animate_step`, and emits a patch after each successful dirty
iteration.  Shape references preserve transform, visibility, face color,
border color, and wire color.  Unsupported presentation kinds fail explicitly
until their snapshot representation is added.

Standalone and headless modes need explicit adapters; they must not infer
process role by importing Qt.  Arbitrary `preanimate` GUI access remains
explicitly unsupported by the managed adapter.

Shape-only legacy assembly trees are now flattened into logical scene
references during managed `display()`. Their existing kinematic methods update
those references after publication, so Pacman, Robot, and the bundled games do
not require runner-side Qt windows or AIS contexts. Supported and excluded
example patterns are listed in
[Managed animation migration notes](managed-animation-migration.md).

## Live updates and input

The accepted live-update design keeps `show(animate=callback)` callbacks in
the isolated runner.  It does not serialize or execute them in the GUI.
Logical scene references keep their common mutation API: before `show()` they
edit the draft, and after the initial scene becomes ready they produce
absolute `ScenePatch` property updates.

Patch v1 is limited to transform, visibility, face color/transparency, and
border/wire style on objects already present in the committed snapshot.  Each
patch carries a generation, scene revision, monotonic sequence, and stable
object IDs.  Patches are idempotent and latest-state-wins: bounded producer
and GUI coalescers may skip intermediate sequences.  The GUI revalidates
generation and revision on its own thread, applies one prepared batch to
GUI-owned AIS objects, and redraws once.

Keyboard and basic mouse input travel in the opposite direction as typed,
versioned `InputEvent` data.  A runner sees ZenCad input state or handlers, not
Qt event objects.  This permits simulations and games without giving scripts
direct access to `DisplayWidget` or the AIS context.

Arbitrary `preanimate` Qt widgets, GUI event monkeypatching, and direct
viewer/AIS access are not part of managed compatibility. Declarative control
panels and live topology add/remove are potential later protocol extensions.
Relative managed camera orbit uses a separate cumulative `CameraAction`
contract; it deliberately remains outside ScenePatch and is specified in
[CameraAction transport v1](camera-action-transport.md). The transport DTO,
validation, coalescing, and runner/GUI animation path are implemented. Input
v1 provides keyboard
edges, persistent key state, mouse position/buttons, and wheel deltas through
the Qt-free `state.input` facade. A bounded writer thread prevents the reverse
pipe from blocking the GUI; only mouse motion is coalescible, while discrete
edges retain order. The exact validation and coalescing rules are documented
in [ScenePatch transport v1](scene-patch-transport.md) and
[InputEvent transport v1](input-event-transport.md), while the accepted
decision and rationale are recorded in
[Runner-driven animation with scene patches and input events](../architecture-council/2026-08-01-scene-patch-input-events.md).

## Cancellation and failure

Cancellation is generation-based.  The supervisor first requests cooperative
cancellation so EvalCache and controlled algorithms can stop cleanly.  After
a bounded grace period it terminates the runner.  Any later messages from that
generation are ignored.

Runner failure never clears the committed scene.  Protocol corruption or an
unsupported object kind is a failed generation with an actionable diagnostic,
not a partial scene.

The implemented `RunnerSupervisor` launches every generation with Python's
`spawn` context, so a runner cannot inherit Qt, window, or OpenGL state from
the GUI process.  The run request and progress/output/error/finished events are
versioned, length-checked JSON frames sent with `Connection.send_bytes`; scene
messages use the existing `ZCSN` binary frame or its atomic file bundle, and
live updates use `ZCPT` frames, and reverse input uses `ZCIN` frames. No Python object is sent through
`Connection.send`.

Starting a generation immediately makes all older messages stale.  Reader
threads may continue draining an older process, but generation filtering occurs
before callback dispatch, so a late scene cannot reach the presenter.  A shared
cancellation event and trace hook stop ordinary Python evaluation
cooperatively.  After the configured grace period, a reaper thread terminates
a runner blocked in native code without blocking the caller or GUI thread.
Missing terminal messages, non-zero process exits, corrupt frames, stdout,
stderr, tracebacks, and EvalCache progress are converted into generation-tagged
`RunnerMessage` values.  The next generation remains startable after every
terminal state.

## Runtime entry points

The default `zencad` application owns a small local Qt shell containing the
editor, console, menus, file watcher, and `RunnerSupervisor`. Its one
`DisplayWidget` is constructed with the main window and never replaced.
Runner callbacks cross into the GUI thread through a queued Qt signal; a
snapshot is staged until that generation reports successful completion and is
then committed by `ScenePresenter`.  Animated snapshots commit on their
ordered `ready` event so their long-lived runner can start feeding patches;
static snapshots still wait for successful `finished`.  Queued patches are
coalesced in a thread-safe bridge before they enter Qt's event queue, validated
against generation and scene revision, and committed to the existing AIS
handles with one redraw.
Progress appears in the status bar while the previous scene remains visible.
Navigation and export actions are routed directly to the local display instead
of a worker-side window.

The normal `zencad SCRIPT.py` entry point always creates this persistent editor
and evaluates scripts through `RunnerSupervisor`. The old worker/frame/sleeping
process modes fail immediately with a migration hint and cannot enter an
embedding branch.

`zencad --display SCRIPT.py` and direct `show()` remain available as an
explicit same-process standalone viewer. They create one local
`DisplayWidget`; they do not launch an editor process or transport a native
window ID. `--no-show` remains a Qt-free same-process evaluation mode.

The display still passes its own native widget handle to OCCT when creating the
platform window. That is local renderer initialization, not cross-process
window transport. No foreign Qt window wrapper or container remains in the
active ZenCad sources.

`utest/gui_reload_smoke.py` exercises 20 successive reloads plus failure,
cancellation, and supersession while asserting stable native-window, viewer,
context, editor, console, and camera identities. `utest/gui_games_smoke.py`
drives Tetris through the reverse input channel, and
`utest/gui_standalone_smoke.py` verifies the local direct-script path.
`utest/runtime_embedding_removal_test.py` guards the removed symbols and legacy
CLI modes. Headless protocol/runtime tests run on Linux, Windows, and macOS in
CI; the native OCCT/X11 GUI smokes run on Linux under Xvfb.
