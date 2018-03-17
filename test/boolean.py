#!/usr/bin/env python3
#coding: utf-8

import sys
sys.path.insert(0, "..")

import zencad
import zencad.solid as solid
import zencad.face as face
from zencad.widget import *

import math

base = solid.box(100,100,100,center=True)

f1 = face.ngon(rad = 35, n = 3).down(50)
f2 = face.ngon(rad = 35, n = 5).rotateY(zencad.gr(90)).left(50)
f3 = face.circle(35).rotateX(zencad.gr(90)).back(50)

s1 = solid.linear_extrude(face = f1, vector = (0,0,100))
s2 = solid.linear_extrude(face = f2, vector = (100,0,0))
s3 = solid.linear_extrude(face = f3, vector = (0,100,0))

m1 = base - s1 - s2 - s3
m2 = base ^ s1 ^ s2 ^ s3
m3 = s1 + s2 + s3

ystep = 200
xstep = 200

display(base.forw(ystep))

display(s1)
display(s2.left(xstep))
display(s3.right(xstep))

display(m1.back(ystep))
display(m2.left(xstep).back(ystep))
display(m3.right(xstep).back(ystep))

show()