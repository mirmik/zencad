#!/usr/bin/env python3
"""
ZenCad API example: revol2
"""

from zencad import *

proto0 = square(10, center=True)
m00 = revol2(profile=proto0, r=20)
m01 = revol2(profile=proto0, r=20, yaw=(0,deg(180)), roll=(0,deg(60)))
m02 = revol2(profile=proto0, r=20, roll=(0,deg(720)))

proto1 = square(10)
m10 = revol2(profile=proto1, r=20)
m11 = revol2(profile=proto1, r=20, yaw=(0,deg(180)), roll=(0,deg(60)))
m12 = revol2(profile=proto1, r=20, n=60, yaw=(0,deg(360)), roll=(0,deg(360)))

hl(proto0)
display(m00)
display(m01.movX(60))
display(m02.movX(120))

hl(proto1.movY(60))
display(m10.movY(60))
display(m11.movX(60).movY(60))
display(m12.movX(120).movY(60))

SECTS = False
N = 120

show()
