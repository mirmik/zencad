#!/usr/bin/env python3
#coding: utf-8

from zencad import *

h = helix(pitch = 20, height = 50, radius = 10)
p = polysegment(points([(10,0,0), (10,0,-10), (5,0,-5)]), closed = True)
#p = wcircle(r=3)

m = pipe_shell(path = h, prof = p, frenet = True)
#m = pipe(path = h, prof = p)

#display(h)
display(p)
display(m)
show()