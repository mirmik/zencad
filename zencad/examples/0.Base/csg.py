#!/usr/bin/env python3
# coding: utf-8

from zencad import *

m1 = box(15, center=True) + sphere(10)
m2 = box(15, center=True) ^ sphere(10)
m3 = box(15, center=True) - sphere(10)

display(m1.left(24))
display(m2)
display(m3.right(24))

show()
