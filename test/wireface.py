#!/usr/bin/env python3
#coding: utf-8

import sys
sys.path.insert(0, "..")

import zencad.solid as solid
import zencad.wire as wire
import zencad.math3
from zencad.widget import *

pnts = zencad.math3.points([
	(0,10,0),
	(7,7,0),
	(10,0,0),
	(0,0,0),
])
w = wire.polysegment(pnts, closed = True)
f = w.face()
#print(pnts)


display(w)
display(f)
show()