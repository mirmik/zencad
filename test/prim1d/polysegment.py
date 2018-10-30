#!/usr/bin/env python3
#coding: utf-8

import sys
sys.path.insert(0, "../..")

import zencad

m = zencad.polysegment(
	[
		(0,0,0),
		(0,10,10),
		(0,10,20),
		(0,-10,20),
		(0,-10,10),
	],
	closed=True
)

zencad.display(m)
zencad.display(m.left(20).fill())

zencad.show()