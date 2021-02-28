#!/usr/bin/env python3
"""
ZenCad API example: widewire
"""

from zencad import *

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

w = widewire(wr.doit(), 5)

disp(wr.doit(), zencad.color.red)
disp(w)
show()
