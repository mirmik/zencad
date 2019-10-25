#!/usr/bin/env python3
"""
ZenCad API example: circle
last update: 04.10.2019
"""

from zencad import *

m0 = circle(r=10)
m1 = circle(r=10, angle=deg(90))
m2 = circle(r=10, angle=(deg(45), deg(90)))

m3 = circle(r=10, wire=True)
m4 = circle(r=10, angle=deg(90), wire=True)
m5 = circle(r=10, angle=(deg(45), deg(90)), wire=True)

pacman = ( 
	circle(r=10, angle=(deg(-135), deg(135))) - 
	circle(r=1).forw(5)
)

disp(m0.right(30), color.red)
disp(m1.right(60), color.green)
disp(m2.right(90), color.white)
disp(m3.right(30).back(30), color.red)
disp(m4.right(60).back(30), color.green)
disp(m5.right(90).back(30), color.white)

disp(pacman.forw(30).right(30), color.yellow)
for w in pacman.wires(): disp(w.forw(30).right(60))

show()
