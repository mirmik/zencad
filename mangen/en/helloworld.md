# Hello Friend.

Here is an example to demonstrate the principle of building models in zencad.
```python
from zencad import *

a = box(200, 200, 200, center = True)
b = sphere(120)
c = sphere(60)

model = a - b + c

display(model)

show()
```

------------------
## What's happening:
```python
from zencad import *
```
In the first line, we import into the current zencad namespace. In this case, we are interested in the `box`,` sphere`, `display`,` show` functions.
</br>
</br>


```python
a = box(200, 200, 200, center = True)
b = sphere(120)
c = sphere(60)
```
Preparing geometric primitives. A box object is created with dimensions 200x200x200 and an offset of the geometric center to the origin. It also creates two spheres with a radius of 120 and 60.
</br>
</br>


```python
model = a - b + c
```
Computing the model using boolean operations. First, a large sphere will be subtracted from the cube. Then a small one was added. The order of the terms is important in this case, since the difference of geometric bodies is non-commutative.
</br>
</br>


```python
disp(model)
```
The `disp` function passes the object into the scene for later display.
</br>
</br>


```python
show()
```
Displaying the scene widget.

---------------------------
## If everything went well:
![](../images/helloworld.png)


## Running and checking a model

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
