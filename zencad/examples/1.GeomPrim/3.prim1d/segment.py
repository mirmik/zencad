#!/usr/bin/env python3

"""
ZenCad API example: segment.py
"""

from zencad import *

m = segment(point3(10, 0, 0), point3(10, 20, 30))
display(m)

show()
