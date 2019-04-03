#!/usr/bin/env python3
# coding: utf-8

from zencad import *

m = circle(10) + square(17, center=True)

m0 = m
m1 = unify(m)
m2 = m.extrude(10)
m3 = unify(m).extrude(10)

display(m0)
display(m1.right(30))
display(m2.forw(30))
display(m3.right(30).forw(30))

show()
