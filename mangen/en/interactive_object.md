# Interactive object

An interactive object is a display unit in zencad.

This section lists the types of interactive objects and specifies the methods of the corresponding base class.

----------------------------------------------
## Geometric interactive objects.
The interactive object engine is used to display geometric shapes processed by zencad.

Example 1 (Creating an interactive form object):
```python3
model = zencad.box(10)
scn = zencad.Scene()

intobj = zencad.display(model, scene=scn)

zencad.show(scn)
```

Example 2 (Create an interactive form object using the disp display function):
```python3
model = zencad.box(10)

intobj = zencad.disp(model)
intobj.set_color(zencad.color.yellow)
```

---------------------------------------
## Methods of the interactive_object class:

### Repositioning
```python3
intobj.relocate(trans)
```
Relocates the object to the _trans_ position relative to its original location.

### Hiding
```python3
intobj.hide(True)
```
Hide or re-display the object. The hidden object is not removed from memory.

### Color setting
```python3
intobj.set_color(color)

# Examples:
# RGB:
intobj.set_color((0.2,0.3,0.6))
intobj.set_color(zencad.Color(0.2,0.3,0.6))

# RGBA:
intobj.set_color((0.2,0.3,0.6,0.5))
intobj.set_color(zencad.Color(0.2,0.3,0.6,0.5))
```
Change the color of the interactive object.
The color parameter represents either a tuple or a zencad.Color object.

## Controlling an object in the editor

A geometry operation creates a new shape. The controller returned by `display()` changes the presentation of an existing scene object:

```python
import zencad as z

with z.managed_scene(1):
    body = z.box(10)
    controller = z.display(body, name="part")
    controller.relocate(z.right(20))
    controller.set_color(z.yellow)
    controller.hide(True)
    assert controller.is_hidden()
    controller.hide(False)
```

`relocate(transform)` sets placement and `location()` reads it; `set_color()`/`color()` update and read color; `hide()`/`is_hidden()` control visibility. Controllers also support transform helpers. Usually set an absolute placement each frame with `relocate` to avoid unintentionally accumulating transforms.

This does not change BREP or perform a boolean operation: the source `body` remains unchanged. Managed animation updates properties of objects created beforehand. Do not construct `interactive_object` or QWidget instances manually to update a model. [Animation](animate.html).

## Graphical interactive objects.
In addition to interactive objects of geometric shapes, there are interactive objects that can be used to transfer additional information on the working stage:

---
### Arrow:

Show an arrow corresponding to the vector _vec_, leading from the point _pnt_, the size of the arrow head is determined by the _arrlen_ parameter, the line width by the _width_ parameter.
Add the object to a scene with `display()`.

```python3
from zencad.interactive.line import arrow

display(arrow(pnt, pnt + vec, color=zencad.white, arrlen=5, width=1))
```

---
### Line:
Show the line, between the points _apnt_ and _bpnt_, line width with the _width_ parameter.
Add the object to a scene with `display()`.

```python3
from zencad.interactive.line import line as display_line

display(display_line(apnt, bpnt, color=zencad.white, width=1))
```

----------------------------------

These functions take start and end points and create display objects; `zencad.line` creates a geometric curve and serves a different purpose.

```python
import zencad as z
from zencad.interactive.line import arrow, line as display_line

with z.managed_scene(1):
    z.display(arrow((0, 0, 0), (10, 0, 0), color=z.red, arrlen=2))
    z.display(display_line((0, 0, 0), (0, 10, 0), color=z.green))
```
