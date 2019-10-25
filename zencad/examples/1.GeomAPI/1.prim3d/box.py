#!/usr/bin/env python3
"""
ZenCad API example: box
"""

from zencad import *

box_a = 10
box_b = 15
box_c = 20

# About center option:
b0 = box(box_a, box_b, box_c)
b0c = box(box_a, box_b, box_c, center=True)
disp(b0, color=color.magenta)
disp(b0c, color=color.cian)

# API variants:
m1 = box(box_a)
m2 = box(box_a, box_b, box_c)
m3 = box(size=(box_a, box_b, box_c))
disp(m1.right(30 * 1), color=color.red)
disp(m2.right(30 * 2), color=color.green)
disp(m3.right(30 * 3), color=color.blue)

show()
