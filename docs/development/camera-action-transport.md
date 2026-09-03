# CameraAction transport v1

This document specifies the implementation contract accepted in
[Managed camera actions for runner-driven animation](../architecture-council/2026-09-03-managed-camera-actions.md).
It extends the persistent-viewer runtime without changing ScenePatch v1.

## Public callback API

Every `ManagedAnimationState` exposes a Qt-free `state.camera` facade. V1
supports:

```python
state.camera.orbit(axis, angle)
```

The axis is normalized after validation and the angle is expressed in radians.
Calls compose in callback order. The facade exposes no camera getters because
the authoritative camera remains in the GUI process.

An orbit request only becomes transport-visible after its callback iteration
finishes successfully. A failed iteration does not publish partial camera
motion, matching the existing dirty ScenePatch boundary.

## Accumulated action state

The facade starts each generation and scene revision with identity cumulative
orbit and action revision zero. Each `orbit()` call left-composes its normalized
quaternion with the accumulated value and increments the action revision.
Equivalent quaternion signs are canonicalized so encoded values are stable.

When the revision has advanced, the runner publishes the newest cumulative
quaternion. It does not enqueue individual deltas. Multiple calls or callback
iterations may therefore collapse into one transport message while preserving
their composed final orientation.

## Wire contract

A dedicated framed message contains:

- protocol version and message type `camera_action`;
- runner generation and committed scene revision;
- strictly increasing transport sequence;
- strictly increasing action revision;
- normalized cumulative orbit quaternion `(w, x, y, z)`.

The implementation must use a frame marker distinct from `ZCPT`, `ZCIN`, and
snapshot/control frames. Unknown or duplicate fields, unsupported versions,
non-finite values, non-unit or ambiguous quaternions, invalid generations and
replayed sequence/action revisions are rejected before GUI application.

Sequence gaps and action-revision gaps are valid. They mean intermediate
states were coalesced, not that requested motion was lost.

## GUI coalescing and application

The GUI bridge retains at most one newest cumulative camera action for the
current generation and scene revision and queues at most one Qt notification.
It never mixes stream identities.

The GUI stores the last accepted cumulative quaternion. For a newer action it
derives the relative quaternion that advances the previous accumulator to the
new one. That delta is applied on the GUI thread to the current camera:

1. capture the current eye, center, up direction, scale, and projection state;
2. rotate `eye - center` and the up direction by the delta;
3. set the new eye and up direction while preserving center and scale;
4. update cached navigation orientation and issue one redraw;
5. commit the cumulative quaternion and sequence only after success.

If application fails, the captured camera state is restored, the accumulated
checkpoint is not advanced, and the current live generation is failed. Scene
objects and the last valid frame remain presented.

## Interaction with navigation

Camera actions are relative to the GUI camera at application time. A user's
orbit, pan, or zoom therefore becomes the base for the next program action.
The runner does not poll or reconstruct that state.

Camera-action production continues while a mouse button is held. Manual drag
events and relative actions are serialized on the GUI thread and compose with
the camera state left by the preceding event. No absolute runner value can
overwrite the manual result, and there is no pause or deferred backlog to
replay after drag.

## Lifecycle

- Initial snapshot commit and its camera policy happen before actions apply.
- Reload and supersession clear the coalescer and last cumulative checkpoint.
- Cancellation closes the producer and discards pending actions.
- Generation or scene-revision mismatches are stale data and touch no camera.
- Runner callback failure leaves the last successfully applied camera state.

## Verification

Protocol tests cover canonical round-trip, malformed frames, quaternion
normalization/canonicalization, non-commuting composition, replay, gaps,
coalescing, bounds, and generation/revision filtering.

Runner tests verify that successful iterations publish accumulated actions,
failed iterations do not, and cancellation/reload resets state. GUI tests
verify transactional application to a fake camera. Native GUI smoke verifies
the `3.Animation/camera.py` scenario, continuous orbit during user drag, and
stable viewer identity across reload, error and cancellation.
