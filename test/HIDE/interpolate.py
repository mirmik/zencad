#!/usr/bin/env python3
#coding: utf-8

import zencad

pnts = zencad.points([
	(0,0),
	(1,0),
	(2,0),
	(4,1),
	(5,2),
	(6,3),
])

tang = zencad.vectors([
	(1,0),
	(0,0),
	(1,0),
	(1,1),
	(1,1),
	(1,1),
])

zencad.display(zencad.interpolate(pnts = pnts))
for p in pnts: zencad.display(p)
zencad.show()