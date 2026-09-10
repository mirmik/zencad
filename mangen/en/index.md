<div class="home-hero">
<h1>ZenCad.</h1>
<p class="home-tagline">Script CAD for righteous programmers.</p>
<img src="../images/generic/zencad-logo.png" alt="ZenCad model: a cube with spherical cutouts">
</div>

## What is ZenCad?
_ZenCad_ is a library for parametric 3D modeling. the library adheres to the idea of ​​creating a 3D model by writing a script and its legs grow from the _OpenScad_ system. Unlike _OpenScad_, the library uses the geometrical core of the boundary representation _OpenCascade_ and the general-purpose language _Python_.

_ZenCad_ can be used as an independent rapid prototyping system for prototyping or 3D printing purposes, and in combination with the libraries of the _Python_ ecosystem, in particular for building 3D models based on calculations performed in such systems as scipy and sympy.

# Fast start.

------------
## Install.
```sh
python3 -m pip install "zencad[gui]"
```

--------------
## Graphic user intrface.
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
## References
github: [https://github.com/mirmik/zencad](https://github.com/mirmik/zencad)  
pypi: [https://pypi.org/project/zencad](https://pypi.org/project/zencad)  
