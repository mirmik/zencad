#!/usr/bin/env python3
#coding: utf-8

from zencad import *
test_mode()

ng = ngon(r = 10, n = 6) 
vtxs = ng.vertices()
m1 = ng.fillet(3, vtxs[0:3])
m2 = ng.fillet(3, vtxs[3:6])
m3 = ngon(r = 10, n = 6).fillet(3)

display(m1)
display(m2.left(30))
display(m3.right(30))

show()