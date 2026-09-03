# Managed camera actions for runner-driven animation

- Date: 2026-09-03
- Status: Accepted
- Kanboard: #2124 `[animation] Определить managed camera command contract`

## Context

The persistent-viewer runtime deliberately keeps the camera, OCCT view, and
Qt navigation in the GUI process. Animation callbacks remain in an isolated
runner and currently update only scene objects through `ScenePatch`.

The legacy `3.Animation/camera.py` callback rotated the viewer's current eye
around the scene and paused while the user dragged the mouse. Replacing that
behaviour with model rotation avoided cross-process camera access, but changed
the meaning of a public example and is not accepted as the final migration.

Camera motion has different delivery semantics from object state. Scene
properties are absolute latest-state values, while a camera orbit must be
relative to the GUI's current camera so that user navigation becomes the new
base instead of being overwritten by runner-owned coordinates.

## Decision

Managed animation gains a separate, Qt-free camera action API and wire stream.
The first public operation is:

```python
state.camera.orbit(axis, angle)
```

`axis` is a finite non-zero three-vector and `angle` is a finite value in
radians. The callback does not receive `DisplayWidget`, `V3d_View`, `eye`, or
any other GUI-owned state.

The runner composes every requested orbit into a normalized cumulative
quaternion. After a successful callback iteration it may publish a versioned
`CameraAction` containing the generation, scene revision, monotonic sequence,
action revision, and newest cumulative orbit. The cumulative value is an
idempotent checkpoint of requested relative motion, not an absolute camera
orientation.

The GUI keeps the last accepted cumulative orbit for the committed generation
and scene revision. When a newer action arrives, it computes the unapplied
relative quaternion between the previous and new cumulative values and applies
that delta to the camera state that exists at that moment:

- rotate the eye offset around the current camera center;
- rotate the camera up direction consistently;
- preserve center, scale, projection mode, and clipping policy;
- redraw once after a successful action.

Because the delta is applied to current GUI state, mouse navigation is never
replaced by a stale runner-side `eye`. Arbitrary-axis composition is retained
even when rotations do not commute. Sequence gaps are valid, duplicate or old
actions are rejected, and a bounded GUI coalescer may retain only the newest
cumulative value without losing final requested motion.

Camera actions use a stream separate from `ScenePatch`. They share the current
runner-to-GUI connection and generation lifecycle, but have their own DTO,
frame marker, sequence, validation, coalescer, queued GUI notification, and
last-applied state. This preserves ScenePatch v1's existing absolute object
property contract and keeps camera failures out of object-patch transactions.

The initial snapshot camera policy establishes the base camera before live
actions begin. Reload, cancellation, supersession, or a new scene revision
clears pending and last-applied camera action state. Stale actions are dropped
before touching the viewer. If validation or GUI application fails, the
pre-action camera is restored and the live generation is cancelled while the
last valid scene remains visible.

The callback remains responsible for deciding when to request motion. The
restored bundled example pauses while a navigation button is held:

```python
def animate(state):
    if not state.input.mouse_buttons:
        state.camera.orbit((0, 0, 1), deg(-0.8))
```

This restores the observable legacy behaviour: the viewer camera orbits the
model, user drag pauses automatic motion, and animation resumes from the
camera orientation chosen by the user. The temporary model-orbit replacement
must be removed from `camera.py`; it may survive only as a separately and
honestly named model-animation example.

## V1 boundary

Camera action v1 includes relative orbit only. It does not include:

- absolute `set_eye`, `set_center`, or `set_scale` commands;
- runner-side camera state reads or GUI-to-runner camera snapshots;
- pan, zoom, fit, projection changes, or mixed camera timelines;
- direct viewer access or arbitrary GUI callbacks.

These operations may be added as separately specified actions. They must not
weaken GUI camera ownership or make delivery unbounded.

## Rationale

Sending absolute camera state would need a reverse camera-state round trip and
would introduce stale-state races with mouse navigation. Sending disposable
relative deltas would lose motion when the GUI coalesces frames, while sending
every delta would allow latency and memory to grow without bound.

A cumulative relative quaternion gives the useful properties of both models:
ordered composition in the runner, idempotent and coalescible transport, and
application relative to the newest GUI-owned camera. A separate stream keeps
these semantics explicit instead of overloading ScenePatch's object-state
contract.

## Consequences

- `ManagedAnimationState` gains a Qt-free camera facade.
- The runner protocol gains a camera-action codec and reporter path.
- The supervisor and main window gain independent camera-action dispatch and
  bounded coalescing.
- `DisplayWidget` gains one transactional relative-orbit application method.
- Unit tests must cover codec validation, quaternion composition, gaps,
  replay, coalescing, stale generations, and reset behaviour.
- GUI smoke must prove that orbit changes the camera without changing model
  transforms, survives coalescing, pauses during drag, resumes from manual
  navigation, and preserves the native viewer across reload/error/cancel.

The concrete transport contract is specified in
[`../development/camera-action-transport.md`](../development/camera-action-transport.md).

