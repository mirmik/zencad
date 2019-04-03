#!/usr/bin/env python3
# coding: utf-8

from zencad import *

test_mode()

m1 = revol(square(10, center=True).rotateX(deg(90)).right(40))
m2 = revol(circle(10).rotateX(deg(90)).right(40))
m3 = revol(ngon(r=10, n=8).rotateX(deg(90)).right(40))

display(m1.left(100))
display(m2)
display(m3.right(100))

show()
