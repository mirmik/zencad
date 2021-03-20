#!/usr/bin/env python3
# coding: utf-8
"""
ZenCad API example: halfspace

Halfspace is special solid that used to boolean operation.
In fact, we can't display halspace, but we can use it for intersection
or for substutution.
"""

from zencad import *

# Substitution example:
m0 = sphere(10)
m1 = m0 - halfspace().rotateY(deg(120))
m2 = m1 - halfspace().mirrorXY().up(3)
m3 = m2 - halfspace().rotateX(deg(-90)).rotateZ(deg(45)).back(3)

disp(m0.right(0))
disp(m1.right(25))
disp(m2.right(50))
disp(m3.right(75))

clr = (0.6, 0.6, 0.8, 0.8)
disp((m0-m1).right(25), color=clr)
disp((m1-m2).right(50), color=clr)
disp((m2-m3).right(75), color=clr)

# Intersection example:
m0 = sphere(10)
m1 = m0 ^ halfspace().rotateY(deg(120))
m2 = m1 ^ halfspace().mirrorXY().up(3)
m3 = m2 ^ halfspace().rotateX(deg(-90)).rotateZ(deg(45)).back(3)

disp(m0.right(0).forw(25))
disp(m1.right(25).forw(25))
disp(m2.right(50).forw(25))
disp(m3.right(75).forw(25))

clr = (0.6, 0.6, 0.8, 0.8)
disp((m0-m1).right(25).forw(25), color=clr)
disp((m1-m2).right(50).forw(25), color=clr)
disp((m2-m3).right(75).forw(25), color=clr)

show()
