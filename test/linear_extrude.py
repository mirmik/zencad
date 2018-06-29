#!/usr/bin/env python3
#coding: utf-8

from zencad import *

import evalcache
evalcache.enable()

pnts = points([
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

f0 = polygon(pnts)
s0 = linear_extrude(f0, (10,1,10))
s1 = linear_extrude(f0, (5,1,10))
s2 = linear_extrude(f0, (0,0,10))

f1 = polygon(pnts).rotateX(gr(10)).up(30)
s3 = linear_extrude(f1, (0,0,10))

display(s0.right(20))
display(s1)
display(s2.left(20))
display(s3.transform(translate(0,0,30) * translate(0,0,40))
	)
show()