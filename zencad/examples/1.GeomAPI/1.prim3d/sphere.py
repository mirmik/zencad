#!/usr/bin/env python3
"""
ZenCad API example: sphere
"""

from zencad import *

m1 = sphere(r=10)
m2 = sphere(r=10, yaw=deg(135))
m3 = sphere(r=10, pitch=(deg(20), deg(60)))
m4 = sphere(r=10, yaw=deg(135), pitch=(deg(10), deg(45)))

display(m1)
display(m2.right(30))
display(m3.right(60))
display(m4.right(90))

# Pacman
pacman = (
	sphere(r=10, yaw=deg(360-45)).rotateY(deg(90)).rotateX(deg(-55))
	- sphere(r=3).move(5,-7,8)
	- sphere(r=3).move(-5,-7,8)
	+ sphere(r=1).move(4,-5,6)
	+ sphere(r=1).move(-4,-5,6)
)
disp(pacman.move(45,50,0), color.yellow)
disp(sphere(r=2).move(45,35,-2))
disp(sphere(r=2).move(45,25,-2))

show()
