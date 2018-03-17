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

display(wire.circle(28).face())
display(face.circle(28).right(40))

f = (wire.circle(28).face() + face.circle(28).right(40)).forw(80)
display(solid.linear_extrude(f, 20))

show()