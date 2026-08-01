# InputEvent transport v1

`InputEvent` is the typed, pickle-free reverse channel from the persistent GUI
to the current managed animation runner. It complements
[ScenePatch transport v1](scene-patch-transport.md): Qt owns event collection,
the runner owns user callbacks, and neither Qt event objects nor widgets cross
the process boundary.

## Callback API

Every managed animation state has `state.input`, an `InputState` containing
persistent state and edges for the current callback iteration:

- `key_down(name)`, `key_pressed(name)`, and `key_released(name)`;
- `mouse_button_down(name)`, `mouse_button_pressed(name)`, and
  `mouse_button_released(name)`;
- `mouse_position`, `mouse_delta`, and accumulated `wheel_delta`;
- normalized `modifiers` and the ordered raw `events` tuple.

Key names are lowercase (`a`, `right`, `space`, `f3`, `page_up`). Mouse button
names are `left`, `middle`, `right`, `back`, and `forward`; modifiers are
`shift`, `control`, `alt`, and `meta`. Persistent down-state survives callback
iterations. Press/release sets, mouse delta, wheel delta, and `events` are
cleared at the start of each iteration. If a press and release arrive together,
both edges are visible while the final down-state is false.

Example:

```python
from zencad import *

controller = display(box(10, center=True))
position = 0

def animate(state):
    global position
    if state.input.key_pressed("right"):
        position += 10
        controller.relocate(translate(position, 0, 0))

show(animate=animate)
```

## Wire contract

A `ZCIN` frame contains protocol version 1, a JSON byte length, and canonical
UTF-8 JSON. Every message carries its runner generation, a strictly increasing
sequence, event type, and type-specific data. The maximum payload is 64 KiB.
Unknown/missing fields, duplicate JSON properties, non-finite coordinates,
invalid names, excessive data, wrong generations, and replayed sequences are
rejected.

The v1 event types are:

- `key_down`, `key_up`: key, text, modifiers, autorepeat flag;
- `mouse_move`: position, held buttons, modifiers;
- `mouse_button_down`, `mouse_button_up`: button, position, modifiers;
- `mouse_wheel`: horizontal/vertical angle delta, position, modifiers.

Qt key and button constants are normalized in the GUI. The runner protocol and
`InputState` modules do not import PyQt.

## Ordering and bounds

Keyboard, mouse-button, and wheel events are ordered edges and are never
silently discarded. Consecutive mouse motion is continuous state and may be
replaced by its newest value. The GUI-side queue retains at most 256 events;
when full it first evicts pending motion, drops new motion if only edges remain,
and reports an explicit error rather than dropping another edge.

An input writer thread drains that queue into a one-way multiprocessing pipe.
Consequently a blocked runner cannot block the Qt event loop. The runner
coalesces currently available motion again before updating `InputState`.

The supervisor accepts events only for its current live, non-cancelled
generation. The runner independently validates generation and ordering.
Cancellation closes the reverse pipe and discards queued input; superseded
input therefore cannot reach the replacement callback.

## Verification

`utest/input_protocol_test.py` covers codec/version/schema/size/order rules,
bounded motion coalescing, edge retention, and state semantics.
`utest/runner_supervisor_test.py` sends key edges through a real spawn-runner
and verifies stale-generation filtering without importing PyQt there.
`utest/gui_reload_smoke.py` sends a Qt key event to move a real displayed
object while its timer continues to service the event loop.
