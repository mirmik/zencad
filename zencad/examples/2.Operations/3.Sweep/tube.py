#!/usr/bin/env python3
"""
ZenCad API example: tube
"""

from zencad import *

POINTS = points([
    (0, 0, 5),
    (0, 0, 20),
    (5, 0, 25),
    (20, 0, 25),
    (25, 5, 25),
    (25, 25, 25),
    (25, 30, 30),
    (25, 30, 50),
    (20, 30, 55),
    (5, 30, 55),
    (0, 30, 50),
    (0, 30, 5),
    (0, 25, 0),
    (0, 5, 0),
])

SPINE = sew([
    segment(POINTS[0], POINTS[1]),
    interpolate([POINTS[1], POINTS[2]], tangs=[(0, 0, 1), (1, 0, 0)]),
    segment(POINTS[2], POINTS[3]),
    interpolate([POINTS[3], POINTS[4]], tangs=[(1, 0, 0), (0, 1, 0)]),
    segment(POINTS[4], POINTS[5]),
    interpolate([POINTS[5], POINTS[6]], tangs=[(0, 1, 0), (0, 0, 1)]),
    segment(POINTS[6], POINTS[7]),
    interpolate([POINTS[7], POINTS[8]], tangs=[(0, 0, 1), (-1, 0, 0)]),
    segment(POINTS[8], POINTS[9]),
    interpolate([POINTS[9], POINTS[10]], tangs=[(-1, 0, 0), (0, 0, -1)]),
    segment(POINTS[10], POINTS[11]),
    interpolate([POINTS[11], POINTS[12]], tangs=[(0, 0, -1), (0, -1, 0)]),
    segment(POINTS[12], POINTS[13]),
    interpolate([POINTS[13], POINTS[0]], tangs=[(0, -1, 0), (0, 0, 1)]),
])

OUTER_SHELL = tube(spine=SPINE, r=3)
INTERNAL_SHELL = tube(spine=SPINE, r=2)

MODEL = make_solid([INTERNAL_SHELL, OUTER_SHELL])
CUTTED_MODEL = MODEL - halfspace() - halfspace().rotX(-deg(90)) - \
    halfspace().rotY(deg(90))

S = 60
disp(MODEL)

disp(CUTTED_MODEL).right(S*1)

disp(INTERNAL_SHELL, color=(0.0, 0.0, 0.8, 0.7)).right(S*2)
disp(CUTTED_MODEL).right(S*2)

disp(INTERNAL_SHELL, color=(0.0, 0.0, 0.8, 0.7)).right(S*3)


show()
