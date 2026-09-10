# Animation, input and camera
The graphical interface allows you to animate the displayed scene.

Editor callbacks run in an isolated runner. The GUI owns the persistent viewer and receives presentation changes. The callback argument is ZenCad state, not a `DisplayWidget`.

Save as `animation.py` and open with `zencad animation.py`:

```python
import zencad as z

controller = z.display(z.box(10, center=True))

def animate(state):
    controller.relocate(z.rotateZ(state.loctime) * z.right(20))
    if state.input.key_pressed("Space"):
        controller.hide(not controller.is_hidden())
    state.camera.orbit((0, 0, 1), z.deg(15) * state.delta)

z.show(animate=animate, animate_step=0.02)
```

`loctime` is elapsed animation time in seconds; `delta` is the frame interval. `start_time`, `time` and `last_time` are also available. `animate_step` requests an interval rather than guaranteeing an exact frame rate; using `delta` makes motion independent of actual frame speed.

`state.input.key_down()` reads a held key; `key_pressed()`/`key_released()` read transitions in the current frame. Ordered events are in `state.input.events`, with mouse position/delta/buttons/wheel state also available. Do not replace Qt handlers manually.

`state.camera.orbit(axis, angle)` requests a relative camera rotation about a world axis in radians. It composes with the current GUI camera and manual mouse navigation. Camera animation does not require model changes.

## Managed scene limits

Create all geometry before `show()`. Callbacks may change placement, color and visibility, but cannot add/remove shapes or replace their BREP payloads. `assemble.unit` trees support relocating existing parts.

`preanimate`, arbitrary QWidget panels and direct viewer access are unsupported in managed runners. `close_handle` is available for animated managed sessions, not static scenes. Standalone display has a separate contract; the example above targets the editor.

`inspect`, `check` and `render` require a final static scene and reject animated `show()`. Details: [managed migration](../development/managed-animation-migration.md).

Here we use a special animation function `animate`, which, using the controller object returned by the disp function, updates the location of the controlled object based on the current moment in time.
The transformation object is used as a parameter of the `relocate` method. (More details in [Transformations](trans0.html), [Transformations](trans1.html))
