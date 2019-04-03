#!/usr/bin/env python3
# coding: utf-8

from zencad import *

test_mode()

box_a = 10
box_b = 10
box_c = 20

m1 = box(size=box_a)
m2 = box(size=(box_a, box_b, box_c))
m3 = box(box_a, box_b, box_c)

m1c = box(size=box_a, center=True)
m2c = box(size=(box_a, box_b, box_c), center=True)
m3c = box(box_a, box_b, box_c, center=True)

display(m1.right(30 * 0))
display(m2.right(30 * 1))
display(m3.right(30 * 2))

display(m1c.right(30 * 3))
display(m2c.right(30 * 4))
display(m3c.right(30 * 5))

show()
