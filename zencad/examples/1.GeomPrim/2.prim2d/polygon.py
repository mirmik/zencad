#!/usr/bin/env python3
"""
ZenCad API example: polygon
"""

from zencad import *

m = polygon([(0,0),(0,10),(20,20),(10,0)])

disp(m)
show()