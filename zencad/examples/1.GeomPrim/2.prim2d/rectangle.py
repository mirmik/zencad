#!/usr/bin/env python3
"""
ZenCad API example: rectangle
last update: 04.10.2019
"""


from zencad import *

m0 = rectangle(a=10, b=6, center=True)
m1 = rectangle(a=10, b=6)
m2 = rectangle(6, center=True)
m3 = square(6)

display(m0, color=color.yellow)
display(m1.up(0.3), color=color.green)
display(m2.forw(10), color=color.red)
display(m3.forw(10).up(0.3), color=color.white)

show()
