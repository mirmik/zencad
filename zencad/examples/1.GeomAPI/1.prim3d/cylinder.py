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

show()
