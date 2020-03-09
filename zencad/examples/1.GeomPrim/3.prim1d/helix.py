#!/usr/bin/env python3
"""
ZenCad API example: helix.py
"""

from zencad import *

m1 = helix(r=10, h=40, step=4)
m2 = helix(r=10, h=40, step=4, left=True)
m3 = helix(r=10, h=40, step=4, angle=deg(10))
m4 = helix(r=10, h=40, step=4, angle=deg(-10))

disp(m1)
disp(m2.right(30))
disp(m3.right(60))
disp(m4.right(90))

show()
