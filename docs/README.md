# dzencad
CAD system for righteous dzen programmers

Install
-------
sudo apt install qt5-default
sudo apt install oce-*
sudo apt install python3-pip
python3 -m pip install dzencad

HelloWorld
----------
```python
#!/usr/bin/env python3.6
#coding: utf-8

import dzencad.solid as solid
from dzencad.widget import *

m = solid.box(10,10,10) + solid.sphere(5).translate(5,5,10)

display(m)
show()
```

![docs/result.jpeg][docs/result.jpeg]

