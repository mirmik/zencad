#!/usr/bin/env python3
# coding: utf-8

from zencad import *

test_mode()

m = sphere(10) - halfspace().rotateY(deg(120))

display(m)

show()
