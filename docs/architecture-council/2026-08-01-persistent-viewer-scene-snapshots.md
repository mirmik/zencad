# Persistent viewer and scene snapshots

- Date: 2026-08-01
- Status: Accepted
- Kanboard: #1211 `[architecture] Перейти к постоянному viewer и замене сцен`

## Context

ZenCad currently creates the OCCT viewer inside the process that evaluates a
user script.  On every iteration the worker publishes a native window handle;
ZenFrame wraps that foreign window with `QWindow.fromWinId()` and inserts it
into the editor.  A new iteration therefore creates and maps another native
window, replaces the embedded container, loses viewer state, and depends on
platform-specific window reparenting.

Moving evaluation to a Python thread in the GUI process would remove the
window boundary, but it would not guarantee a responsive interface.  Pure
Python work contends for the GIL, long extension calls may retain it, and an
arbitrary stuck script cannot be stopped safely as a thread.

## Decision

ZenCad will use two distinct runtime roles:

1. One long-lived GUI process owns `QApplication`, `MainWindow`,
   `DisplayWidget`, `V3d_View`, `AIS_InteractiveContext`, all AIS presentation
   objects, camera state, selection, and interaction.
2. An isolated, replaceable runner process evaluates one script generation,
   performs geometric computation, and produces a versioned scene snapshot.

The runner never creates a Qt window or an AIS context.  The GUI never embeds
a foreign native window.  The process boundary carries scene data, progress,
stdout/stderr, and errors, not Qt, AIS, or native-window objects.

The initial snapshot protocol is explicit and does not pickle Python objects.
It contains:

- protocol version and generation identifier;
- ordered objects with stable snapshot-local identifiers;
- object kind and an OCCT-neutral payload reference;
- BREP bytes for `TopoDS_Shape` geometry;
- color, transparency, boundary/wire style, visibility, and transform;
- scene-level presentation policy such as `preserve`, `fit`, or an explicit
  camera request.

`display()` builds a runner-local, data-only scene draft.  `show()` freezes the
draft and publishes a snapshot when running under the managed runner.  AIS
objects are materialized only in the GUI process.

The GUI validates and decodes the complete snapshot before commit.  A commit
runs on the GUI thread without an intermediate redraw: remove the previous
scene presentation, display the new objects with updates disabled, then issue
one viewer update.  The previous successful scene remains visible while a new
generation is computing or when that generation fails.

Camera state is preserved by default.  The first scene may fit automatically;
later snapshots fit only when explicitly requested.  Selection may initially
be cleared on commit and can later be preserved through stable object IDs.

Every run has a monotonically increasing generation ID.  Messages and
snapshots from superseded generations are ignored.  Cancellation first asks
the runner to stop cooperatively; after a grace period the supervisor may
terminate and replace that runner without affecting the GUI or the last good
scene.

## Rationale

This division keeps the two properties that justify a process boundary:
fault/GIL isolation and hard cancellation.  It removes the properties that
made the old model fragile: cross-process window ownership, repeated OpenGL
initialization, and viewer replacement.  BREP is slower than sharing an
in-process `TopoDS_Shape`, but it is explicit, inspectable, portable across the
local process boundary, and already supported by ZenCad's OCP compatibility
layer.

## Alternatives considered

### Evaluate on the GUI thread

Rejected because ordinary model construction would block the Qt event loop.

### Evaluate in a Python thread

Rejected as the primary runtime because GIL behaviour of arbitrary Python and
extension calls cannot guarantee responsiveness, and a stuck thread cannot be
terminated safely.

### Keep embedding a viewer from each runner

Rejected because it preserves native-window races, platform coupling, viewer
state loss, and repeated rendering initialization.

### Send pickled scene and OCP objects

Rejected because it creates an implicit, unsafe, implementation-coupled
protocol and does not provide a stable representation for native OCCT handles.

## Consequences and risks

- Geometry crosses the boundary by value, so BREP encode/decode latency and
  memory use must be measured before choosing pipe frames versus file-backed
  blobs for large scenes.
- `Scene` and interactive objects currently construct AIS objects eagerly;
  they must be split into runner-side descriptions and GUI-side presentation.
- Imported user modules remain naturally isolated when each generation gets a
  fresh runner.  Prewarming is an optimization, not part of protocol
  correctness.
- Arbitrary animation callbacks cannot cross this boundary.  Animation and
  live interaction require a later versioned `ScenePatch`/command contract or
  an explicitly reduced compatibility contract.
- BREP transfer preserves topology but not every custom Python-side behaviour.
  Supported scene object kinds and fallback diagnostics must be explicit.
- Materializing very large AIS scenes can still occupy the GUI thread; the
  implementation needs timing instrumentation and a loading state.

## Follow-up work

1. Specify and benchmark the snapshot wire format and BREP transport.
2. Split runner-side scene descriptions from GUI-side AIS presentation.
3. Introduce a permanent viewer and transactional `ScenePresenter`.
4. Add runner supervision, generation filtering, cancellation, and diagnostics.
5. Integrate the snapshot pipeline while retaining the last successful scene.
6. Decide and implement animation/live-update compatibility.
7. Remove `bindwin`, `QWindow.fromWinId()`, `createWindowContainer()`, and the
   legacy unbound viewer path after compatibility tests pass.

The planned runtime contract is described in
[`../development/runtime-architecture.md`](../development/runtime-architecture.md).
