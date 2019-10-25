#!/usr/bin/env python3
"""
ZenCad API example: sphere
"""

from zencad import *

m1 = sphere(r=10)
m2 = sphere(r=10, yaw=deg(135))
m3 = sphere(r=10, pitch=(deg(20), deg(60)))
m4 = sphere(r=10, yaw=deg(135), pitch=(deg(10), deg(45)))

display(m1)
display(m2.right(30))
display(m3.right(60))
display(m4.right(90))

show()
