#!/usr/bin/env python3
#coding: utf-8

import sys
sys.path.insert(0, "../..")

import dzencad.solid as solid
from dzencad.widget import *
import dzencad.cache
import math

dzencad.cache.enable("dzencache")

m1 = solid.box(10,10,10)
m2 = solid.box(10,10,10).translate(5,5,5)

display((m1 + m2).right(20))
display((m1 - m2).left(20))
display((m1 ^ m2))

(m1 ^ m2).dump("temporary.bin")

show()