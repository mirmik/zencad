#!/usr/bin/env python3
#coding: utf-8

import zencad

m1 = zencad.ngon(r = 10, n = 6).fillet(3, (3,4,5))
m2 = zencad.ngon(r = 10, n = 6).fillet(3, (0,1,2))
m3 = zencad.ngon(r = 10, n = 6).fillet(3)
zencad.display(m1)
zencad.display(m2.left(30))
zencad.display(m3.right(30))

zencad.show()