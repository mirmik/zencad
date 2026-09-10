# Displaying geometry

## display and disp

`display` adds geometry to the scene. `disp` is its short name. The returned controller lets you change the object's [placement, color and visibility](interactive_object.html).

```python
from zencad import *

controller = display(box(10), color=Color(0.2, 0.6, 0.8), name="housing")
show()
```

For a list, `display` returns a list of controllers; for an assembly `unit`, it returns the unit itself. Names passed through `name=` belong to individual objects and must be unique within the scene. They appear in [inspect](headless.html) reports.

## Color

`Color(r, g, b, a=0)` accepts components from 0 to 1. The first three specify RGB; the fourth is transparency: 0 is opaque and 1 is fully transparent.

```python
from zencad import *

display(box(10), color=Color(0.2, 0.6, 0.8, 0.5))
display(sphere(3).right(15), color=yellow)
show()
```

Predefined colors include `white`, `black`, `red`, `green`, `blue`, `yellow`, `magenta`, `cian`, `mech` and `transmech`. They are also available through the `zencad.color` module.

## highlight and hl

Highlighting adds a shape to the scene and returns the shape itself. This is useful for showing a cutting volume directly within an expression:

```python
from zencad import *

body = box(20) - hl(cylinder(4, 20).translate(10, 10, 0))
display(body)
show()
```

## show and an explicit scene

`show()` displays the assembled scene. When the editor runs the script, the result appears in its window; running `python model.py` directly opens a separate viewer.

The default scene is normally used. You can create your own when needed:

```python
from zencad import *

scene = Scene()
scene.add(box(10), color=blue)
display(sphere(3).right(15), color=yellow, scene=scene)
show(scene)
```

`scene.add()` also returns an object controller. The `animate` and `animate_step` parameters of `show` are described in [Animation](animate.html); see [ZenCad internals](internal.html) for how display works.
