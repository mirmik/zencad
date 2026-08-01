# ScenePatch transport v1

This document records the implemented, pickle-free protocol foundation for
the accepted
[runner-driven animation design](../architecture-council/2026-08-01-scene-patch-input-events.md).
It defines transport and coalescing. Runner production and transactional GUI
application are implemented.

## Runner lifecycle

Managed `show()` publishes the initial `SceneSnapshot`, emits
`ready(scene_revision=0, animated=true)`, and then runs the callback inside the
same isolated spawn-runner. The Qt-free callback state retains the legacy
timing fields. Mutations through the logical object returned by `display()`
are coalesced by object and property during each callback iteration; only a
successfully completed iteration is drained into the next sequence.

Patch writes are synchronous, so the runner cannot build an unbounded frame
queue behind a slow consumer. Callback failures become structured runner
errors and leave the last completely emitted state intact. Cancellation and
supersession stop the live generation through the existing cooperative trace
and bounded hard-cancel fallback. `preanimate` and direct GUI access are
explicitly outside this managed lifecycle.

## GUI application

The main window commits an animated snapshot on its ordered `ready` event,
while static snapshots retain the stronger rule of waiting for successful
runner completion. Incoming patches are merged by a thread-safe
`ScenePatchCoalescer` bridge before entering Qt's event queue. At most one GUI
notification remains queued while newer absolute state accumulates behind it;
the supervisor also disables patch history recording for GUI sessions. The
presenter checks generation, scene revision, sequence, and every object ID
before touching AIS state.

Transform, visibility, face/transparency, boundary, and wire changes are
applied to the existing AIS handles. A batch performs one viewer update. If
any operation fails, all touched handles are restored to their previous state
and the live runner is cancelled; later data from that failed generation is
ignored. Full scene replacement still owns camera policy, so ordinary patches
leave the camera and native viewer unchanged.

## Wire contract

A `ZCPT` frame contains a protocol version, JSON byte length, and canonical
UTF-8 JSON payload. The payload identifies its type, version, runner
generation, committed scene revision, monotonic sequence, and object updates.
The maximum encoded frame is 4 MiB and one patch may address at most 100,000
objects. Object IDs are non-empty UTF-8 strings of at most 512 bytes.

Every object update carries one or more absolute values from this fixed v1
set:

- `transform`: complete scale, quaternion rotation, and translation;
- `visible`: boolean presentation state;
- `color`: RGBA face color, where alpha is OCCT transparency;
- `border_color`: RGBA face-boundary style;
- `wire_color`: RGBA wire style.

Numeric values must be finite, scale and the rotation quaternion must be
non-zero, and RGBA components must be in `[0, 1]`. Unknown or missing fields,
malformed JSON, non-finite numbers, duplicate JSON properties, duplicate
object IDs, excessive sizes, and unsupported versions are rejected before a
`ScenePatch` is returned.

Within one patch an object may occur once and a property may occur once.
Across strictly increasing patch sequences, later absolute properties replace
earlier values. Sequence gaps are explicitly valid.

## Coalescing

`ScenePatchCoalescer` retains at most a configured number of objects. It merges
new values by object and property and emits one patch carrying the newest
observed sequence. Draining clears pending values but preserves stream
identity and sequence ordering. Mixing generations or scene revisions,
replaying a sequence, or exceeding the configured object bound is an error;
callers explicitly clear the coalescer when switching scenes.

This policy bounds memory without requiring every visual frame to be shown.
It does not silently discard an object's latest unapplied state: if the
configured object capacity is insufficient, the producer receives an error.

## Stale filtering

`ensure_current_scene_patch()` compares generation and scene revision before
GUI-side object lookup or materialization. A mismatch raises
`SupersededScenePatchError`; stale data can therefore be dropped without
touching AIS objects.

## Verification

`utest/scene_patch_protocol_test.py` covers canonical round-trip, immutable
DTOs, malformed/unknown/duplicate input, property and resource limits,
generation/revision filtering, sequence gaps, latest-state coalescing, and
bounded/mixed-stream failure modes. `utest/scene_draft_test.py` verifies
post-publication dirty state, and `utest/runner_supervisor_test.py` verifies
ready/patch ordering, structured callback failure, and cancellation. The
suites import no Qt modules in the runner process. `utest/scene_presenter_test.py`
covers GUI-thread guards, sequence/revision/object validation, stable handles,
single redraw, and rollback. `utest/gui_reload_smoke.py` exercises real X11
pixels and persistent window/view/context/camera identities across reload and
live animation. The same smoke now drives that animation through a real
[`InputEvent`](input-event-transport.md) key edge.
