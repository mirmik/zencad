#!/usr/bin/env python3
"""
ZenCad API example: scale
"""

from zencad import *

a = sphere(10)

m0 = a.scale(1.5)
m1 = a.scaleXYZ(1.3, 2, 0.5)
m2 = a.scaleX(1.5)
m3 = a.scaleY(1.5)
m4 = a.scaleZ(1.5)

disp(m0.movX(0))
disp(m1.movX(30))
disp(m2.movX(60))
disp(m3.movX(90))
disp(m4.movX(120))

show()
