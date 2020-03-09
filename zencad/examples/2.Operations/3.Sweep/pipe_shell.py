#!/usr/bin/env python3
"""
ZenCad API example: revol2
"""

from zencad import *

a=circle(r=20)
#b=ngon(10, n=5).up(40)
b = circle(r=10).up(10)

#disp(extrude(a,5))
#disp(extrude(b,5))

#show()

#print(a.normal())
#print(b.normal())

wires = [
	circle(r=10, wire=True).up(0),
	circle(r=10, wire=True).up(10),
	circle(r=10, wire=True).up(20),
	circle(r=10, wire=True).up(40),
	circle(r=10, wire=True).up(50)
]

spine = interpolate([(0,0,0), (0,0,10), (20,0,50)])

m = pipe_shell(wires, spine, frenet=True, transition=1)

disp(m)
show()