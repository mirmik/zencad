#!/usr/bin/env python3
# coding: utf-8

from zencad import *

m0 = cone(r1=10, r2=5, h=20)
m1 = cone(r1=10, r2=5, h=20, yaw=deg(90))

m0c = cone(r1=10, r2=5, h=20, center=True)
m1c = cone(r1=10, r2=5, h=20, yaw=deg(90), center=True)

display(m0.right(30 * 0))
display(m1.right(30 * 1))

display(m0c.right(30 * 3))
display(m1c.right(30 * 4))

show()
