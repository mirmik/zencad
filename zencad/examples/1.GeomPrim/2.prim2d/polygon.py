#!/usr/bin/env python3
"""
ZenCad API example: polygon
"""

from zencad import *

m = polygon([point3(0, 0), point3(0, 10), point3(20, 20), point3(10, 0)])

disp(m)
show()
