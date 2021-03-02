#!/usr/bin/env python3
"""
ZenCad API example: short_rotate
last update: 24.10.2019

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
from zencad.interactive import arrow, line

u = 20

# Parameters
angle = deg(60)
arrl, arrw, arrh = 2, 1, 15

src = points([
    (-1, -2, 1),
    (1, -2, 1),
    (-2, 1, 0),
])

tgt = points([
    (1, 2, 1),
    (1, 1, 0),
    (2, 2, 3)
])

clr = [color.red, color.green, color.blue]

# Scale
for i in range(len(src)):
    for j in range(3):
        src[i][j] *= u
        tgt[i][j] *= u

# Make short rotate transformation
transes = [translate(*src[i]) * short_rotate((0, 0, 1),
                                             tgt[i] - src[i]) for i in range(len(src))]

# Make cylinders geometry
cyl = cylinder(r=5, h=10, center=True)
tgt_cyls = [trans(cyl) for trans in transes]

# Draw cylinders
for t in tgt_cyls:
    disp(t)

# Draw arrows
for i in range(len(src)):
    arr = arrow(src[i], tgt[i], arrlen=arrl, width=arrw, color=clr[i])
    disp(arr)

# Draw white cube.
N = 4
for i in range(N):
    for j in range(N):
        for k in range(N):
            if i < N-1:
                disp(line(point3(i*u, j*u, k*u), point3(i*u+u, j*u, k*u)))
            if j < N-1:
                disp(line(point3(i*u, j*u, k*u), point3(i*u, j*u+u, k*u)))
            if k < N-1:
                disp(line(point3(i*u, j*u, k*u), point3(i*u, j*u, k*u+u)))

for i in range(len(tgt)):
    if tgt[i] in src:
        disp(textshape("BOOM!!!!", os.path.join(zencad.moduledir, "examples/fonts/mandarinc.ttf"),
                       20, True).rotateX(deg(90)).translate(*tgt[i]).up(15), color=color.red)

show()
