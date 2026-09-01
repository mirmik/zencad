#!/usr/bin/env python3
"""
ZenCad API example: rotate_array
"""

from zencad import *
import math


def radial_array(shape, count, sweep=2 * math.pi, endpoint=False):
    divisor = count - 1 if endpoint else count
    return [shape.rotateZ(sweep * index / divisor) for index in range(count)]

a = box(15, center=True) 
b = cylinder(r=15, h=10)
c = ellipse(10,5)
d = square(10, center=True, wire=True)

k1 = unify(union(radial_array(a.right(25), 6)))
k2 = unify(union(radial_array(a.right(25), 4, deg(180), endpoint=True)))
k3 = unify(union(radial_array(a.right(25), 4, deg(180))))
k4 = unify(union(radial_array(a.right(25).rotX(deg(-90)), 4, deg(180), endpoint=True)))

m1 = unify(union(radial_array(b.right(20), 6)))
m2 = unify(union(radial_array(c.rotZ(deg(90)).right(20), 12)))
m3 = radial_array(d.right(20), 60, deg(270), endpoint=True)

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
