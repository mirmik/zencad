#!/usr/bin/env python3

from zencad import *
m = box(20)
m = thicksolid(m, 1, [point3(0, 5, 5)])

disp(m)
show()
