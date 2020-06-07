#!/usr/bin/env python3
"""
ZenCad API example: interpolate2
last update: 06.07.2020
"""

from zencad import *

POINTS = points2([
		[(0,0,0), (10,0,7), (20,0,5)],
		[(0,5,0), (10,5,7.5), (20,5,7)],
		[(0,10,2), (10,10,8), (20,10,5)],
		[(0,15,1.3), (10,15,8.5), (20,15,6)],
	])

m = interpolate2(POINTS)
disp(m)
disp(POINTS, color=color.red)

show()
