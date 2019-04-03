#!/usr/bin/env python3
# coding: utf-8

from zencad import *

m0 = circle(r=10)
m1 = circle(r=10, angle=deg(90))
m2 = circle(r=10, angle=(deg(45), deg(90)))

m3 = circle(r=10, wire=True)
m4 = circle(r=10, angle=deg(90), wire=True)
m5 = circle(r=10, angle=(deg(45), deg(90)), wire=True)

display(m0.right(30 * 0))
display(m1.right(30 * 1))
display(m2.right(30 * 2))
display(m3.right(30 * 3))
display(m4.right(30 * 4))
display(m5.right(30 * 5))

show()
