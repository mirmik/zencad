#!/usr/bin/env python3
"""
ZenCad API example: short_rotate
last update: 13.10.2019

Detail:
Short rotate application example.

That operation very useful if you need rotate object axis 
by source axis vector and target axis vector. 
Otherwise, With common rotation operation you should evaluate 
rotation axis and rotation angle.

In that example you can play with `src` and `tgt` arrays.
Practice shooting :).
"""

from zencad import *
import zencad.draw

# Parameters
angle = deg(60)
arrl, arrw, arrh = 2, 2, 15

src = points([
	(-20,-40,20),
	(20,-40,0),
	(-40,20,0),
])

tgt = points([
	(20,40,40),
	(20,20,40),
	(20,40,20)
])

clr = [ color.red, color.green, color.blue ]

# Make short rotate transformation
transes = [ translate(*src[i]) * short_rotate((0,0,1), tgt[i] - src[i]) for i in range(len(src)) ]

# Make cylinders geometry
cyl = cylinder(r=5, h=10, center=True)
tgt_cyls = [ trans(cyl) for trans in transes ]

# Draw cylinders
for t in tgt_cyls:
	disp(t)

# Draw arrows
for i in range(len(src)):
	arr = zencad.draw.arrow(pnt=src[i], vec=tgt[i]-src[i], arrlen=arrl, width=arrw, clr=clr[i])
	disp(arr)

# Draw white cube.
u = 20
N = 4
for i in range(N):
	for j in range(N):
		for k in range(N):
			if i < N-1: 
				disp(zencad.draw.line(point3(i*u,j*u,k*u), point3(i*u+u,j*u,k*u)))
			if j < N-1: 
				disp(zencad.draw.line(point3(i*u,j*u,k*u), point3(i*u,j*u+u,k*u)))
			if k < N-1: 
				disp(zencad.draw.line(point3(i*u,j*u,k*u), point3(i*u,j*u,k*u+u)))

for i in range(len(tgt)): 
	if tgt[i] in src:
		disp(textshape("BOOM!!!!", os.path.join(zencad.moduledir, "examples/fonts/mandarinc.ttf"), 20, True).rotateX(deg(90)).translate(*tgt[i]).up(15), color=color.red)

show()
