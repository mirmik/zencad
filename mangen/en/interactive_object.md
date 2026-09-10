# Interactive objects

The controller returned by `display()` manages how geometry is displayed. Moving or hiding it does not change the original shape.

## Placement, color and visibility

```python
from zencad import *

body = box(10)
controller = display(body)
controller.relocate(right(20))
controller.set_color(yellow)
controller.hide(True)
controller.hide(False)
show()
```

| Method | Action |
| --- | --- |
| `relocate(transform)` | Set placement relative to the original position |
| `location()` | Get placement |
| `set_color(color)` | Change color |
| `color()` | Get color |
| `hide(True)`, `hide(False)` | Hide or show |
| `is_hidden()` | Check whether the object is hidden when running in the editor |

Colors can be `Color` objects or RGB/four-component tuples. The fourth component is transparency. `set_color` also accepts `border_color` for face boundaries and `wire_color` for lines.

In animations, setting the full placement with `relocate` avoids accumulating transforms from frame to frame. When running in the editor, you can change properties of existing objects; creating new geometry inside a callback is not supported. See [Animation](animate.html).

## Arrows and lines

Graphic objects help show directions and auxiliary constructions. Add them to the scene with `display()`:

```python
from zencad import *
from zencad.interactive.line import arrow, line as display_line

display(arrow((0, 0, 0), (10, 0, 0), color=red, arrlen=2, width=2))
display(display_line((0, 0, 0), (0, 10, 0), color=green, width=2))
show()
```

Both functions accept start and end points. `width` sets line thickness; `arrlen` sets the arrowhead size. To draw a vector `vec` from a point `pnt`, use `arrow(pnt, pnt + vec)`.

Here, `display_line` names the graphic function. The `line` function in the main ZenCad API creates a geometric curve.
