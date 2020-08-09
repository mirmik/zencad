#!/usr/bin/env python3
"""
ZenCad API example: widecurve
"""

from zencad import *

zencad.lazy.fastdo = True
zencad.lazy.encache = False
zencad.lazy.decache = False

#w = interpolate([
#	point3(0,0),
#	point3(10,0),
#	point3(20,10),
#])

wr = wire_builder()
wr.line(10,10)
wr.line(20,20)
wr.line(30,0)
wr.interpolate([
	[40, -20],
	[30, -40]
])
wr.interpolate([
	[50, -60],
	[60, -110]
])

w = widecurve(wr.doit(), 5)

disp(wr.doit(), zencad.color.red)
disp(w)
show()
