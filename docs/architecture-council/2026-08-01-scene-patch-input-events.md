# Runner-driven animation with scene patches and input events

- Date: 2026-08-01
- Status: Accepted
- Kanboard: #1218 `[animation] Определить ScenePatch protocol`

## Context

The persistent-viewer runtime evaluates each script in an isolated runner and
transfers a complete `SceneSnapshot` to the GUI.  This is sufficient for
static scenes, but the legacy animation API keeps a Python callback alive and
lets it mutate AIS-backed interactive objects from a `QThread`.  Some examples
also receive the real display widget through `preanimate`, create arbitrary Qt
windows, or replace GUI event handlers.

Callbacks, Qt widgets, AIS objects, and native windows cannot safely cross the
process boundary.  Running callbacks in the GUI process would also surrender
GIL isolation and hard cancellation.  Removing animation altogether would
discard useful ZenCad programs, including assemblies and interactive games.

## Decision

Animation remains runner-driven.  The callback passed to
`show(animate=..., animate_step=...)` stays as an ordinary Python object inside
the current generation's runner and is never serialized.  After publishing
and preparing the initial `SceneSnapshot`, the runner remains alive, invokes
the callback, and reports logical object mutations as versioned
`ScenePatch` messages.

The managed object returned by `display()` is a logical facade compatible with
the supported `InteractiveObject` mutation API.  Before `show()`, calls such
as `relocate()`, `transform()`, `set_color()`, and `hide()` modify the
`SceneDraft`.  Once the initial scene is ready, the same calls update
runner-local state and mark absolute properties dirty for the next patch.

The initial patch contract supports only existing-object property updates:

- transform;
- visibility;
- face color and transparency;
- border and wire style.

Each patch identifies the protocol version, generation, scene revision,
monotonic sequence, and updates keyed by stable scene object ID.  Values are
absolute and idempotent.  Sequence gaps are valid: intermediate animation
states may be dropped when the producer is faster than the viewer.

Patch delivery is bounded and coalescing.  The runner must not accumulate an
unbounded frame queue; unsent dirty properties are merged with the newest
absolute state.  The GUI similarly retains only the newest compatible pending
state and applies patches at a bounded refresh rate.  It validates the current
generation and scene revision again on the GUI thread, prepares all updates,
applies them to GUI-owned AIS objects without intermediate redraws, and issues
one viewer update.

User input uses the reverse, typed channel.  The GUI sends versioned
`InputEvent` values for the current generation.  The first contract includes
keyboard press/release and basic mouse position, buttons, and wheel data.  The
runner exposes this through a ZenCad-owned input state and/or handlers; it does
not receive Qt event objects.  Ordered edge events are retained, while
continuous state may be coalesced.

An animation callback failure stops that live session and leaves the last
valid presented state visible.  Reload or cancellation invalidates both patch
and input streams for the old generation and may terminate its runner.

Arbitrary PyQt imports, custom Qt widgets, direct `DisplayWidget`/AIS access,
GUI method replacement, and legacy `preanimate` behaviour are outside the
managed compatibility contract.  Existing interactive examples may be ported
to ZenCad input events without changing their game or geometry logic.
Declarative control panels may be designed separately; they are not required
for the first animation milestone.

## Rationale

Keeping callbacks in the runner preserves fault isolation, GIL isolation, and
hard cancellation while retaining the natural Python animation model.  The
logical interactive facade keeps common scripts source-compatible and creates
one interception point for both draft construction and live mutation.

Absolute, coalescible property patches match rendering semantics: displaying
every computed intermediate frame is less important than bounding latency and
showing the newest state.  A typed input channel is enough for interactive
games without exposing Qt implementation details or allowing a script to
mutate the GUI from another thread.

## Alternatives considered

### Static scenes only

Rejected because it removes a useful and established ZenCad capability.

### GUI-owned declarative timelines only

Not selected as the primary compatibility path.  It is deterministic and
could be added later, but it would require most existing procedural animation
code to be rewritten and is poorly suited to simulations and games.

### Execute callbacks in the GUI process

Rejected because it reintroduces GIL contention, GUI stalls, unsafe arbitrary
code execution beside Qt, and the inability to terminate a stuck callback.

### Preserve arbitrary `preanimate` and real Qt widget access

Rejected because this would require executing user GUI code in the GUI
process or transporting non-serializable Qt objects across the process
boundary.  Both contradict the persistent-viewer ownership model.

### Send every animation frame in order

Rejected because a paused or slower GUI would create unbounded latency and
memory growth.  Absolute updates make bounded latest-state delivery safe.

## Consequences and risks

- The runner becomes long-lived for an animated generation and needs an
  explicit `ready`/live-session lifecycle distinct from static `finished`.
- `SceneDraft` references must support a post-publication dirty-state phase.
- Assemblies must flatten to stable logical object references rather than AIS
  objects in the runner.
- `ScenePresenter` needs an object-ID index and transactional property-update
  support.
- Patch and input paths require independent size, rate, sequence, generation,
  and scene-revision validation.
- A bounded writer/coalescer is required so a blocked transport cannot grow
  memory or stall simulation logic indefinitely.
- Existing examples that touch PyQt or the real viewer need explicit ports.
- Live topology replacement, add/remove, camera commands, declarative control
  panels, and reconnect/checkpoint semantics remain future extensions.

## Follow-up work

1. Specify and test the `ScenePatch` wire format and coalescing rules.
2. Extend runner-side scene references to record dirty property state after
   the initial snapshot.
3. Keep animated runners alive and define ready/error/cancel lifecycle events.
4. Apply validated patches through `ScenePresenter` on the GUI thread.
5. Add the typed `InputEvent` channel and runner-side input facade.
6. Port representative transform, style, assembly, and game examples.
7. Remove the foreign-window compatibility runtime after replacement smokes
   pass.

The planned live-update contract is summarized in
[`../development/runtime-architecture.md`](../development/runtime-architecture.md).
