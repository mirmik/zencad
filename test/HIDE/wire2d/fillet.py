#!/usr/bin/env python3
#coding: utf-8

import sys
sys.path.insert(0, "../..")

import zencad
import zencad.wire as wire
import zencad.face as face
import zencad.solid as solid
from zencad.widget import *
from zencad import gr, pnt

base = face.rectangle(100, 200).fillet(50)

v = zencad.vertex(50,100,150)
b1 = base.up(50)
b2 = base.up(100)
b0 = face.circle(200)

m = solid.loft([b0, b1, b2, v])
display(m)
#display(solid.linear_extrude(p.fillet(30), (0,0,60)))


show()