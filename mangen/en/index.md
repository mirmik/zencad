<div class="home-hero">
<h1>ZenCad.</h1>
<p class="home-tagline">Scripted CAD for righteous programmers.</p>
<img src="../images/generic/zencad-logo.png" alt="ZenCad model: a cube with spherical cutouts">
</div>

## What is it?

ZenCad is a library for parametric 3D modeling. It follows the idea of creating a 3D model by writing a script, with roots in OpenSCAD. Unlike OpenSCAD, it uses the OpenCascade boundary-representation geometry kernel and the general-purpose Python language.

ZenCad can be used on its own for rapid prototyping, mockups and 3D printing, or together with the Python ecosystem—for example, to build models from calculations made in SciPy and SymPy.

Development and installation instructions are on the [Installation](installation.html) page.

# Quick start

------------
## Installation
```sh
python3 -m pip install "zencad[gui]"
```

--------------
## Starting the graphical interface
```sh
zencad

# alternate:
python3 -m zencad
```

-------------
## HelloWorld
```python
#!/usr/bin/env python3
#coding: utf-8

from zencad import *

box = box(200, 200, 200, center = True)
sphere1 = sphere(120)
sphere2 = sphere(60)

model = box - sphere1 + sphere2

display(model)
show()
```

---------
## Links
github: [https://github.com/mirmik/zencad](https://github.com/mirmik/zencad)<br>
pypi: [https://pypi.org/project/zencad](https://pypi.org/project/zencad)
