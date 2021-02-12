#!/usr/bin/env python3

"""
ZenCad API example: bspline.py
# https://pages.mtu.edu/~shene/COURSES/cs3621/NOTES/spline/B-spline/bspline-ex-1.html
# https://en.wikipedia.org/wiki/B-spline
"""

from zencad import *

knots_total = 5
m0 = bspline(
	poles = points([(0, 0, 0), (0, 10, 0), (10, 10)]),
	knots = [ i * 1 / (knots_total-1) for i in range(knots_total) ],
	muls = [1] * knots_total,
	degree=1
)

knots_total = 6
m1 = bspline(
	poles = points([(0, -10, 0), (0, 10, 0), (20, 10)]),
	knots = [ i * 1 / (knots_total-1) for i in range(knots_total) ],
	muls = [1,1,1,1,1,1],
	degree=2
)

knots_total = 7
m2 = bspline(
	poles = points([(0, -10), (0, 10), (10, 10), (10, 30)]),
	knots = [ i * 1 / (knots_total-1) for i in range(knots_total) ],
	muls = [1]*knots_total,
	degree=2
)

disp(m0.moveX(10), color=(0,0,1))
disp(m1.moveX(10), color=(0,1,0))
disp(m2.moveX(10), color=(1,0,0))

show()
