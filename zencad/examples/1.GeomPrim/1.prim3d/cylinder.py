#!/usr/bin/env python3
# coding: utf-8

from zencad import *

m0 = cylinder(r=10, h=20)
m1 = cylinder(r=10, h=20, yaw=deg(90))

m0c = cylinder(r=10, h=20, center=True)
m1c = cylinder(r=10, h=20, yaw=deg(90), center=True)

display(m0.right(30 * 0))
display(m1.right(30 * 1))

display(m0c.right(30 * 2))
display(m1c.right(30 * 3))

#Mr. Cylinder
mister_cylinder = union([
	cylinder(r=10, h=20),
	cylinder(r=5, h=5).up(20),
	cylinder(r=2, h=12, center=True).rotateY(deg(90)).back(10).up(6),
	cylinder(r=2, h=2, center=True).rotateX(deg(90)).back(10).up(14).moveX(5),
	cylinder(r=2, h=2, center=True).rotateX(deg(90)).back(10).up(14).moveX(-5),
])
disp(mister_cylinder.move(45,60,0))

show()
