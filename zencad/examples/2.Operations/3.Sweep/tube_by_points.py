#!/usr/bin/env python3
"""Build a rounded hollow tube from a polyline control-point list."""

from zencad import *


POINTS = [
    (0, 0, 0),
    (0, 0, 30),
    (25, 0, 50),
    (65, 0, 50),
    (85, 20, 50),
    (85, 55, 50),
]

spine = rounded_polysegment(POINTS, r=10)
outer = pipe_shell([circle(5, wire=True)], spine, frenet=True, solid=True)
inner = pipe_shell([circle(3, wire=True)], spine, frenet=True, solid=True)

disp(outer - inner)
disp(spine, color.green)
disp(points(POINTS), color.red)
show()
