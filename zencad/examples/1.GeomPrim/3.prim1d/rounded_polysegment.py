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

m = rounded_polysegment(POINTS, r=10)

disp(m)
for p in POINTS: disp(point3(p), color.red)

show()