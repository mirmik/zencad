#!/usr/bin/env python3
"""
ZenCad API example: revol2
"""

from zencad import *

wires = [
	circle(r=20,wire=True),
	square(30,center=True,wire=True).rotX(deg(30)).movZ(40)
]

spine = interpolate([(0,0,0), (0,0,10), (20,0,40)])

m = pipe_shell(wires, spine, frenet=True, parallel=(0,0,1), binormal=(0,0,0), discrete=False)

disp(m)
show()