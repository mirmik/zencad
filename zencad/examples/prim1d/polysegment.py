#!/usr/bin/env python3
# coding: utf-8

from zencad import *

test_mode()

pnts = points([(0, 0, 0), (0, 10, 10), (0, 10, 20), (0, -10, 20), (0, -10, 10)])

m0 = polysegment(pnts)
m1 = polysegment(pnts, closed=True)
m2 = polysegment(pnts, closed=True).fill()
m3 = polysegment(pnts + [(0, 0, 0)])
m4 = polysegment(pnts + [(0, 0, 0)]).fill()

display(m0)
display(m1.left(20))
display(m2.left(40))
display(m3.left(20).forw(30))
display(m4.left(40).forw(30))

show()
