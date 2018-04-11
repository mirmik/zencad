#!/usr/bin/python3
#coding: utf-8

import sys
sys.path.insert(0, "../..")

import zencad

m = zencad.polysegment(
	zencad.points([
		(0,0,0),
		(10,20,30),
		(10,10,20)
	])
)
zencad.display(m)

zencad.show()