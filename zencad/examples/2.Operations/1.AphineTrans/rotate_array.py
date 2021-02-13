#!/usr/bin/env python3
"""
ZenCad API example: rotate_array
"""

from zencad import *
import zencad.internal_models

a = box(15, center=True) 
b = cylinder(r=15, h=10)
c = ellipse(10,5)
d = square(10, center=True, wire=True)

k1 = rotate_array(n=6, unit=True)(a.right(25))
k2 = rotate_array(n=4, yaw=deg(180), endpoint=True, unit=True)(a.right(25))
k3 = rotate_array(n=4, yaw=deg(180), endpoint=False, unit=True)(a.right(25))
k4 = rotate_array2(n=4, r=25, yaw=(0,deg(180)), roll=(0,deg(-60)), endpoint=True, unit=True)(
	a.rotX(deg(-90)))

m1 = unify(rotate_array(n=6)(b.right(20)))
m2 = rotate_array2(n=12, r=20)(c.rotZ(deg(90)))
m3 = rotate_array2(n=60, r=20, yaw=(0,deg(270)), roll=(0,deg(360)), array=True)(d)

S = 70

disp(b).forw(S)
disp(c).right(S).forw(S)
disp(d).right(S*2).forw(S)

disp(m1).right(0).forw(S*2)
disp(m2).right(S).forw(S*2)
for m in m3: disp(m).right(S*2).forw(S*2)

disp(k1).forw(0)
disp(k2, color.red).right(S).forw(0)
disp(k3, color.green).right(S*2).forw(0)
disp(k4, color.blue).right(S*3).forw(0)
show()
