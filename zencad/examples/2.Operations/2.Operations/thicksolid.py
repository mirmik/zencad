#!/usr/bin/env python3

from zencad import *
from zencad.geom.offset import _shapefix_solid

m = box(20)
m = thicksolid(m, refs=[(0, 5, 5)], t=1)

disp(m)
show()
