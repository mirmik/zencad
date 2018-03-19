#!/usr/bin/env python3
#coding: utf-8

import sys
sys.path.insert(0, "..")

import zencad
import zencad.solid as solid
import zencad.face as face
import zencad.wire as wire
import zencad.math3
from zencad.widget import *

import math

pnts = zencad.math3.points([
	(0,0),
	(0,20),
	(5,20),
	(10,10),
	(15,20),
	(20,20),
	(20,0),
	(15,0),
	(15,15),
	(10,5),
	(5,15),
	(5,0),	
])

f0 = face.polygon(pnts)
s0 = solid.linear_extrude(f0, (10,1,10))
s1 = solid.linear_extrude(f0, (5,1,10))
s2 = solid.linear_extrude(f0, (0,0,10))

f1 = face.polygon(pnts).rotateX(zencad.gr(10)).up(30)
s3 = solid.linear_extrude(f1, (0,0,10))

display(s0.right(20))
display(s1)
display(s2.left(20))
display(s3.right(40))
show()