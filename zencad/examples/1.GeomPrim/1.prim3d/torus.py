#!/usr/bin/env python3
"""
ZenCad API example: torus
"""

from zencad import *

tor_r1 = 5
tor_r2 = 2
tor_u = deg(135)
tor_v1 = deg(-90)
tor_v2 = deg(180)

m0 = torus(r1=tor_r1, r2=tor_r2)
m1 = torus(r1=tor_r1, r2=tor_r2, yaw=tor_u)
m2 = torus(r1=tor_r1, r2=tor_r2, pitch=(tor_v1, tor_v2))
m3 = torus(r1=tor_r1, r2=tor_r2, pitch=(tor_v1, tor_v2), yaw=tor_u)

display(m0.right(20 * 0))
display(m1.right(20 * 1))
display(m2.right(20 * 2))
display(m3.right(20 * 3))

show()
