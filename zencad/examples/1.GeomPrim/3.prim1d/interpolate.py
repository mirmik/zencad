#!/usr/bin/env python3

from zencad import *

m = interpolate([
    point3(0, 0),
    point3(10, 0),
    point3(20, 10),
    point3(0, 5, 10),
],
    tangs=[
        None,
    None,
        None,
    None
])

disp(m)
show()
