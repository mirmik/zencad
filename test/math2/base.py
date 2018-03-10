#!/usr/bin/env python3
#coding: utf-8

import sys
sys.path.insert(0, "../..")

import dzencad.solid as solid
from dzencad.widget import *
from dzencad.math3 import point
from dzencad.wire import segment, polysegment
import math

a = point(-1,1,0)
b = point(1,1,0)
c = point(1,-1,0)
d = point(-1,-1,0)

display(polysegment([a,b,c,d], closed = True))

#m = solid.box(10,10,10)
show()