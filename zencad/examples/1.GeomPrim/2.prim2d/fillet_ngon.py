#!/usr/bin/env python3
# coding: utf-8

from zencad import *
ng = ngon(r=10, n=6)
radius = 4
radius2 = 8

# Fillter all vertices
m1 = ngon(r=10, n=6).fillet2d(radius)

# Generator can be used for array filtering
m2 = ng.fillet2d(radius, [v.point() for v in ng.vertices() if v.point().value()[0] < 0])

# Selections are ordinary typed domain collections.
m3 = ng.fillet2d(radius, [v.point() for v in ng.vertices() if v.point().value()[1] < 0])

# One more syntax variant (and inaccuracy of float when comparing)
m4 = ng.fillet2d(radius, [v.point() for v in ng.vertices() if abs(v.point().value()[1]) < 0.001])

# Advanced version with indexing of sorted array of points
vtxs = sorted(ng.vertices(), key=lambda vertex: tuple(reversed(vertex.point().value()[:2])))
m5 = fillet2d(ng, radius, [vtxs[0].point(), vtxs[3].point(), vtxs[4].point()])
m5 = fillet2d(m5, radius2, [vtxs[1].point(), vtxs[2].point(), vtxs[5].point()])

display(m1)
display(m2.right(30))
display(m3.right(60))
display(m4.right(90))
display(m5.right(120))

show()
