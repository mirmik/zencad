#!/usr/bin/env python3
#coding: utf-8

import sys
sys.path.insert(0, "../..")

import zencad
import zencad.solid as solid
import zencad.face as face
import zencad.wire as wire
import zencad.math3
from zencad.widget import *

import math

m = face.square(30).fillet(6).wires()[0]
exp = m.vertexs()

for i in range(len(exp)):
	print(exp[i])
	display(exp[i])

display(m)

show()