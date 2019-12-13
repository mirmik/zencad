#!/usr/bin/env python3

"""
ZenCad API example: bezier.py
"""

from zencad import *

pnts = points([(0, 0, 0), (0, 10, 0), (10, 10)])

m0 = bezier(pnts)
m1 = bezier(pnts, weights=[1,2,1])
m2 = bezier(pnts, weights=[1,3,1])

disp(m0, color=(1,0,0))
disp(m1, color=(0,1,0))
disp(m2, color=(0,0,1))
disp(pnts)

show()
