#!/usr/bin/env python3

import case
import organizer
from zencad import *

w = 27
h = 20
l = 64
t = 1.5
r = 27 / 2 - 4
z = 1
s = 0.965

d = 5
d2 = 5

m = 3
n = 5

st = organizer.organizer(m, n, w, h, l, t, d, d2)
cs = case.case(w, h, l, t, r, z, s)

ucs = union(
    [
        cs.translate(t * 1.5 + (w + t) * i, 0, t + (h + t) * j)
        for i in range(0, m)
        for j in range(0, n)
    ]
)

disp(ucs)
disp(st, color=(1, 1, 1))
show()
