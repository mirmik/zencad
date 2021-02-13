#!/usr/bin/env python3
"""
ZenCad API example: extrude
"""

from zencad import *

base = ngon(10,6)

m = extrude(base, 10)

disp(m)
show()