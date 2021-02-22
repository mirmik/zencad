#!/usr/bin/env python3
# coding: utf-8

from zencad import *

print("HelloWorld!")

a = box(200, 200, 200, center=True)
b = sphere(120)
c = sphere(60)

model = a - b + c

display(model)

show()
