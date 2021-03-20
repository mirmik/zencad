#!/usr/bin/env python3
"""
ZenCad API example: ngon
last update: 04.10.2019
"""

from zencad import *

m0 = ngon(r=10, n=3)
m1 = ngon(r=10, n=5)
m2 = ngon(r=10, n=8)
m3 = ngon(r=10, n=256)

disp(m0)
disp(m1.right(30))
disp(m2.right(60))
disp(m3.right(90))

NMin = 3
NMax = 12

for i in range(NMin, NMax + 1):
    k = (i-NMin) / (NMax - NMin)
    disp(ngon(r=10, n=i).right((i-NMin)*30).forw(30), Color(k**2, k, 1-k))

show()
