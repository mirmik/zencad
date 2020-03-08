#!/usr/bin/env python3
# coding: utf-8

from zencad import *

arr = [
	circle(r=20, wire=True),
	ellipse(30, 25, wire=True).up(20),
	circle(r=20, wire=True).up(40),
	circle(r=15, wire=True).up(50),
	circle(r=16, wire=True).up(60),
]

m0 = loft(arr)
m1 = loft(arr, smooth=True, maxdegree=10, shell=True)
m2 = loft(arr, smooth=True, maxdegree=10)
m3 = thicksolid(loft(arr, smooth=True, maxdegree=10), refs=[(0,0,60)], t=-2)

disp(m0)
disp(m1).right(80)
disp(m2).right(160)
disp(m3).right(240)

for w in arr: disp(w, color.red).right(80)

show()