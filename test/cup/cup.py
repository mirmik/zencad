#!/usr/bin/env python3
#coding: utf-8

import sys
sys.path.insert(0, "../..")

import dzencad.solid as solid
from dzencad.widget import *
import math

def cup(r,h,t,rr,wr):
	return (
		solid.torus(rr,wr).rotateY(math.pi/2).forw(r).up(h/2)
		- 
		solid.cylinder(r,h) 
		+
		solid.cylinder(r, h) - solid.cylinder(r-t, h-t).up(t)
	)
m = cup(40,90,3.5,25,5)

display(m)
#display(solid.box(1,1,1))
show()