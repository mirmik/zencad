#!/usr/bin/env python3

from zencad import *

m = interpolate([
    (0, 0),
    (10, 0),
    (20, 10),
    (0, 5, 10),
],
    tangs=[
        None,
    None,
        None,
    None
])

disp(m)
show()
