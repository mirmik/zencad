#!/usr/bin/env python3
#coding: utf-8

import sys
sys.path.insert(0, "../..")

import zencad.wire as wire
from zencad.widget import *
from zencad import gr, pnt

#a = wire.arc(100, gr(90), gr(180))
#b = wire.arc(100, gr(270), gr(360))
#c = wire.segment()

display(wire.arc_by_points(pnt(0,0), pnt(20,20), pnt(40,20)))
#display((0,0))
#display((20,20))
#display((40,20))
#display(wire.circle(100, arc_a = gr(270), arc_b = gr(360)))

show()