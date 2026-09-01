#!/usr/bin/env python3
"""Build a hollow tube along a smooth spine with ``pipe_shell``."""

from zencad import *


spine = interpolate(
    [point3(0, 0, 0), point3(0, 0, 35), point3(20, 0, 55), point3(45, 15, 65)],
    tangs=[vector3(0, 0, 1), None, None, vector3(1, 1, 0)],
)

outer = pipe_shell([circle(6, wire=True)], spine, frenet=True, solid=True)
inner = pipe_shell([circle(4, wire=True)], spine, frenet=True, solid=True)
tube = outer - inner

disp(tube)
disp(spine, color.red)
show()
