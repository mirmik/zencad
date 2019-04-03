#!/usr/bin/env python3
# coding: utf-8

from zencad import *

test_mode()

m1 = helix(r=10, h=40, step=4)
m2 = helix(r=10, h=40, step=4, left=True)
m3 = helix(r=10, h=40, step=4, angle=deg(10))
m4 = helix(r=10, h=40, step=4, angle=deg(-10))

display(m1)
display(m2.right(30))
display(m3.right(60))
display(m4.right(90))

show()
