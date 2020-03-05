#!/usr/bin/env python3
"""
ZenCad API example: revol
"""


from zencad import *

# Make revols:
a1 = square(10, center=True)
a2 = circle(10)
a3 = ngon(r=10, n=8)

b1 = a1.rotateX(deg(90)).right(40)
b2 = a2.rotateX(deg(90)).right(40)
b3 = a3.rotateX(deg(90)).right(40)

m1 = revol(b1)
m2 = revol(a2, r=40)
m3 = revol(b3)

# Display revols:
display(m1.left(110), color=color.mech)
display(m2, color=color.mech)
display(m3.right(110), color=color.mech)

# Display it step by step:
display(m1.left(110).forw(110), color=color.transmech)
display(m2.forw(110), color=color.transmech)
display(m3.right(110).forw(110), color=color.transmech)
display(b1.left(110).forw(110))
display(b2.forw(110))
display(b3.right(110).forw(110))
display(a1.left(110).forw(110))
display(a2.forw(110))
display(a3.right(110).forw(110))

# Sector option example:
y1 = revol(b1, yaw=math.pi)
y2 = revol(b2, yaw=math.pi/2)
y3 = revol(b3, yaw=-math.pi)
display(y1.left(110).forw(220))
display(y2.forw(220))
display(y3.right(110).forw(220))

show()
