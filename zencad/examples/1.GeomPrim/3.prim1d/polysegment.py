#!/usr/bin/env python3

"""
ZenCad API example: polysegment.py
"""

from zencad import *

pnts = points([(0, 0, 0), (0, 10, 10), (0, 10, 20), (0, -10, 20), (0, -10, 10)])

m0 = polysegment(pnts)
m1 = polysegment(pnts, closed=True)
m2 = polysegment(pnts, closed=True).fill()
m3 = polysegment(pnts + [(0, 0, 0)])
m4 = polysegment(pnts + [(0, 0, 0)]).fill()

disp(m0)
disp(m1.left(20))
disp(m2.left(40))
disp(m3.left(20).forw(30))
disp(m4.left(40).forw(30))

show()
