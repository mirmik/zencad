# Your first model

Save this complete script as `model.py`:

```python
import zencad as z

body = z.box(20, 10, 4)
hole = z.cylinder(2, 4).translate(10, 5, 0)
part = (body - hole).solids().only()
z.display(part, name="bracket", color=z.green)
z.show()
```

Geometry uses millimetres and angles use radians; `z.deg(90)` converts degrees to radians. Shape operators `+`, `-` and `^` mean union, difference and intersection. Operations return new objects. A boolean operation may return an OCCT container; `.solids().only()` explicitly selects its single solid for `--solid`. If there are several solids, select the required one or display them separately.

Open the model in the editor:

```sh
zencad model.py
```

Saving reruns the script. The persistent viewer keeps its window while the computation process can be replaced on reload or failure.

To check the model without a GUI:

```sh
zencad inspect model.py --json
zencad check model.py --valid --solid
```

`display()` adds the result to the scene; `show()` finishes declaring a static scene in the managed runner. Headless tools need a displayed result to inspect. [Next: value types](prim0d.html).
## A model built from a cube and spheres

This example builds a shape with a sequence of boolean operations:

```python
import zencad as z

a = z.box(200, 200, 200, center=True)
b = z.sphere(120)
c = z.sphere(60)
model = a - b + c
z.display(model)
z.show()
```

Cube `a` is centered at the origin. Sphere `b` cuts out its central region;
sphere `c` adds a separate element at the center. The difference `a - b` is
computed first, followed by union with `c`. Difference depends on operand order.
`display()` adds the result to a scene; `show()` starts presentation or publishes
the scene in the editor's computation process.

![Result of the cube and spheres construction](../images/helloworld.png)
