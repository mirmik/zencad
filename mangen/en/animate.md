# Animation, input and camera
The graphical interface can animate the displayed scene.

The animation function receives timing, input events and camera controls. It changes the state of objects created before `show()`.

Save this as `animation.py` and open it with `zencad animation.py`:

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

`loctime` is the time since animation started, in seconds; `delta` is the frame interval. `start_time`, `time` and `last_time` are also available. `animate_step` sets the desired interval, not a guaranteed frame rate; movement based on `delta` is independent of the actual frame rate.

`state.input.key_down()` reads a held key; `key_pressed()` and `key_released()` report transitions in the current frame. Ordered events are available through `state.input.events`; mouse input includes position/delta/buttons/wheel. Do not replace Qt handlers manually.

`state.camera.orbit(axis, angle)` rotates the camera relative to its current position around a world axis, with the angle in radians. It works with the current GUI camera and combines with manual mouse rotation. The camera can be animated without changing the model.

## Animation in the editor

Create all geometry before `show()`. The callback can change placement, color and visibility, but cannot add/remove shapes or replace their BREP. `assemble.unit` trees support placement changes of existing parts.

When running in the editor, `preanimate` and direct access to Qt widgets are not supported. `close_handle` is called when the animated session ends.

`inspect`, `check` and `render` expect a finite static scene, so they reject animated `show()`. Details: [managed migration](../development/managed-animation-migration.md).
