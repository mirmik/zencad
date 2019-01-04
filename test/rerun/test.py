#!/usr/bin/env python3
#coding: utf-8

from zencad import *
lazy.diag=True

base = box(200, 200, 200, center = True)
sphere1 = sphere(120)
sphere2 = sphere(60)

union = base - sphere1 + sphere2

display(union)
show()