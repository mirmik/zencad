#!/usr/bin/env python3
"""
ZenCad API example: tube_by_points
"""

from zencad import *

POINTS = [
	(0,0,0),
	(0,0,20),
	(0,20,40),
	(-90,20,40),
	(-90,20,20),
	(0,20,0),
]
spine = rounded_polysegment(POINTS, r=10)

a, a_start, a_finish = tube(spine, r=5, bounds=True) 
b, b_start, b_finish = tube(spine, r=3, bounds=True)

c = a_start.fill() - b_start.fill()
d = a_finish.fill() - b_finish.fill()

m = sew([a,b,c,d])

disp(m)
disp(a).forw(60)
disp(spine, color.green).forw(120)
ctrs = disp(points(POINTS), color.red)
for c in ctrs: c.forw(120)
show()
