#!/usr/bin/env python3
#coding: utf-8

from zencad import *

POINTS = [
	(0,0,0),
	(0,0,20),
	(0,20,40),
	(-90,20,40),
	(-90,20,20),
	(0,20,0),
]

POINTS2 = [(0,0), (20,0), (20,20)]

m0 = rounded_polysegment(POINTS, r=10)
m1 = rounded_polysegment(POINTS, r=10, closed=True)
m2 = rounded_polysegment(POINTS2, r=5, closed=True).fill()

disp(m0)
disp(m1.moveY(40),color=color.green)
disp(m2.moveY(80),color=color.yellow)

for p in POINTS: disp(point3(p), color.red)
for p in POINTS: disp(point3(p).moveY(40), color.red)
for p in POINTS2: disp(point3(p).moveY(80), color.red)

show()