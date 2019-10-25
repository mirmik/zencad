#!/usr/bin/env python3
"""
ZenCad API example: cone
"""

from zencad import *

# Basic and centered variants:
m0 = cone(r1=10, r2=5, h=20)
m1 = cone(r1=10, r2=5, h=20, center=True)
disp(m0, color=color(1,0,1,0.5))
disp(m1, color=color(0,1,1,0.5))

# Sector of cone:
m = cone(r1=10, r2=5, h=20, yaw=deg(90))
disp(m.left(30))

# Reversed cone:
m = cone(r1=5, r2=10, h=20)
disp(m.right(30))

# Sharp cone:
m0 = cone(r1=10, r2=0, h=20)
m1 = cone(r1=0, r2=10, h=20)
disp(m0.move( 0, 30, 0))
disp(m1.move(30, 30, 0))

show()
