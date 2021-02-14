#!/usr/bin/env python3
"""
ZenCad API example: extrude
"""

from zencad import *

base = ngon(10,6)

m0 = extrude(base, 10)
m1 = extrude(base, (5,0,10))
m2 = extrude(base, (5,5,10))

disp(m0)
disp(m1.forw(30))
disp(m2.forw(60))
show()