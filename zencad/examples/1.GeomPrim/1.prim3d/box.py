#!/usr/bin/env python3
"""
ZenCad API example: box
"""

from zencad import *

box_a = 10
box_b = 15
box_c = 20

# About center option:
b0 = box(box_a, box_b, box_c)
b0c = box(box_a, box_b, box_c, center=True)
disp(b0, color=color.magenta)
disp(b0c, color=color.cian)

# API variants:
m1 = box(box_a)
m2 = box(box_a, box_b, box_c)
m3 = box(size=(box_a, box_b, box_c))
disp(m1.right(30 * 1), color=color.red)
disp(m2.right(30 * 2), color=color.green)
disp(m3.right(30 * 3), color=color.blue)

# Mister Cube:
mister_cube = (
	box(40, center=True)
	- box(8, center=True).translate(10,-20,8)
	- box(8, center=True).translate(-10,-20,8)
	+ box(4, center=True).translate(10,-18,8)
	+ box(4, center=True).translate(-10,-18,8)
	- box(20, 8, 4, center=True).translate(0,-20,-8)
	+ box(8, center=True).translate(24,0,0)
	+ box(8, center=True).translate(-24,0,0)
	+ box(8, center=True).translate(10,0,-24)
	+ box(8, center=True).translate(-10,0,-24)
	+ box(20,20,10, center=True).rotateZ(deg(40)).translate(1,0,25)
	+ box(30,30,10, center=True).rotateZ(deg(40)).translate(1,0,35)
)

disp(mister_cube.translate(50,100,28))

show()
