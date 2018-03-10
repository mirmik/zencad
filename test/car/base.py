#!/usr/bin/env python3
#coding: utf-8

import sys
sys.path.insert(0, "../..")

import dzencad.solid as solid
from dzencad.widget import *
import math

z = 3

x = 160
y = 160

x2 = 20
y2 = 40

r = 3
lr = 20

def multi(m):
	m = (m + m.mirrorXZ())
	return (m + m.mirrorYZ())

m = solid.box(x, y, z).translate(-x/2, -y/2, 0)
m2 = solid.box(x2, y2, z).translate(x/2 - x2, y/4 - y2/2, 0)
m3 = solid.cylinder(r, z)
m3 = m3 + m3.translate(0,lr,0)
m3 = m3.translate(x / 2 - x2 - 3*r, y/4 - lr/2, 0)

display(m - multi(m2) - multi(m3))
show() 