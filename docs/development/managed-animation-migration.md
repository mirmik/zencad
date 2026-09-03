# Managed animation migration notes

ZenCad's default application now evaluates animation callbacks in an isolated
runner and presents their updates in one persistent GUI-owned viewer. Callback
code remains ordinary Python, but it receives ZenCad state rather than a real
`DisplayWidget`.

## Supported callback API

`show(animate=callback, animate_step=..., close_handle=...)` retains its public
shape. The callback argument provides the timing fields `start_time`, `time`,
`last_time`, `delta`, and `loctime`, plus the Qt-free
[`state.input`](input-event-transport.md) facade. A separate cumulative
[`state.camera`](camera-action-transport.md) facade for relative viewer-camera
orbit.

Objects returned by `display()` retain these live operations:

- `relocate()` and inherited transform helpers;
- `set_color()` including transparency, border, and wire colors;
- `hide()` and `is_hidden()`;
- `color()` and `location()` queries.

Shape and triedron-line `zencad.assemble.unit` trees are flattened into stable
logical scene objects. Existing `unit.relocate()`, rotators, spherical rotators, and
`location_update()` continue to propagate transforms to those objects. The
runner creates no Qt window or AIS context.

Topology is fixed after the initial `show()`: callbacks may change existing
object properties but may not add/remove shapes or replace their BREP payloads.

## Input-driven games

Managed games should read keys from `state.input` instead of importing PyQt or
replacing `DisplayWidget.keyPressEvent`. Persistent movement can use
`key_down()`; one-shot actions can use `key_pressed()` or ordered
`state.input.events` (which also exposes autorepeat presses).

The bundled games now use this model:

- `MiniGames/tetris.py`: arrows move, rotate, and hard-drop the active piece;
- `MiniGames/tennis.py`: left/right arrows control player one, A/D player two.

Both run entirely in the animation runner. Tetris no longer needs a `QMutex`
because calculation and input handling occur serially in the callback. Tennis
replaces its external slider window with keyboard controls.

## Example status

| Scenario | Managed status | Notes |
| --- | --- | --- |
| `3.Animation/base.py` | Supported | Transform patches |
| `3.Animation/color.py` | Supported | Dodecahedron color/transparency patches |
| `3.Animation/pacman.py` | Supported | Assembly transforms and visibility |
| `4.Assemble/robot.py` | Supported contract | Shape-only nested assembly animation |
| `MiniGames/tetris.py` | Supported | InputEvent arrows, visibility/color patches |
| `MiniGames/tennis.py` | Supported | Two-player keyboard input and assembly motion |
| `3.Animation/camera.py` | Supported | `state.camera.orbit(...)` continuously rotates the GUI-owned camera and composes with mouse navigation |
| `4.Assemble/manual-control.py` | Supported | Number keys select a joint; arrows rotate it |
| `4.Assemble/manual-control-2.py` | Supported | Keyboard-driven inverse-kinematics target |

Arbitrary custom QWidget panels remain outside the managed runner contract.
Interactive examples use transported input events instead, so they work in the
same persistent viewer as ordinary scripts.

## Verification

`utest/managed_examples_test.py` runs base transform, color, Pacman, Tetris, and
Tennis through real spawn-runners, requires an animated scene and live patch,
then verifies cooperative cancellation. `utest/gui_games_smoke.py` loads the
real Tetris example in the persistent viewer, sends a Qt arrow key through
`InputEvent`, observes a newer patch without replacing AIS handles/window/view/
context, and checks that a fast Qt timer remains responsive.
