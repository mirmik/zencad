#!/usr/bin/env python3
#coding: utf-8

import sys
sys.path.insert(0, "../..")

import zencad.solid as solid
from zencad.widget import *
from zencad.math3 import point
from zencad.wire import segment, polysegment
import math

a = point(-1,1,0)
b = point(1,1,0)
c = point(1,-2,0)
d = point(-1,-1,0)

ff = polysegment([a,b,c,d], closed = True).face()

display(ff)

#m = solid.box(10,10,10)
show()