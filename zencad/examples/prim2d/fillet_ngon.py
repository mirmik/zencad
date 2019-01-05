#!/usr/bin/env python3
#coding: utf-8

from zencad import *
test_mode()

m1 = ngon(r = 10, n = 6).fillet(3, (3,4,5))
m2 = ngon(r = 10, n = 6).fillet(3, (0,1,2))
m3 = ngon(r = 10, n = 6).fillet(3)

display(m1)
display(m2.left(30))
display(m3.right(30))

show()