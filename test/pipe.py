#!/usr/bin/env python3
#coding: utf-8

import sys
sys.path.insert(0, "..")

import zencad
from zencad import pnt, gr
import zencad.solid as solid
import zencad.face as face
import zencad.wire as wire
import zencad.math3
from zencad.widget import *

import math

#base = face.square(10, center = True).fillet(3)
arc1 = wire.circle(r = 10, arc = (gr(0), gr(90))).right(20)
arc2 = wire.circle(r = 10, arc = (gr(90), gr(180)))

wr = wire.make_wire([arc2, wire.segment(pnt(0,10), pnt(20,10)), arc1]).rotateX(gr(90)).right(10).up(40)
wr = wire.make_wire([wr, wire.segment(pnt(0,0), pnt(0,0,40)), wire.segment(pnt(40,0), pnt(40,0,40))])

prof = face.square(10, center = True).fillet(3)

m = solid.pipe(wr, prof)

display(m)
show()