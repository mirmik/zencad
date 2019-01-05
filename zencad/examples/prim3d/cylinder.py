#!/usr/bin/env python3
#coding: utf-8

from zencad import *
disable_cache()
lazy.diag = True

m0 = cylinder(r=10, h=20)
m1 = cylinder(r=10, h=20, angle=deg(90))
m2 = cylinder(r=10, h=20, angle=(deg(45),deg(90)))

m0c = cylinder(r=10, h=20, center=True)
m1c = cylinder(r=10, h=20, angle=deg(90), center=True)
m2c = cylinder(r=10, h=20, angle=(deg(45),deg(90)), center=True)

display(m0.right(30*0))
display(m1.right(30*1))
display(m2.right(30*2))

display(m0c.right(30*3))
display(m1c.right(30*4))
display(m2c.right(30*5))

show()