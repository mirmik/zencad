#!/usr/bin/env python3
# coding: utf-8

from zencad import *
import evalcache
import functools


ng = ngon(r=10, n=6)
radius = 4
radius2 = 8

# Fillter all vertices
m1 = ngon(r=10, n=6).fillet2d(radius)

# Generator can be used for array filtering
m2 = ng.fillet2d(radius, [v for v in ng.vertices() if v.x < 0])

# We can use lazy lambda for improve caching algorithm
m3 = ng.fillet2d(radius, lazy(lambda: [v for v in ng.vertices() if v.y < 0])())

# One more syntax variant (and inaccuracy of float when comparing)
m4 = ng.fillet2d(radius, evalcache.select(ng.vertices(), lambda v: abs(v.y) < 0.001))

# Advanced version with indexing of sorted array of points
def comparator(a, b):
    """sort by yx_order"""
    xdiff = a.x - b.x
    ydiff = a.y - b.y
    if abs(ydiff) > 0.001:
        return ydiff
    if abs(xdiff) > 0.001:
        return xdiff
    return 0
vtxs = sorted(ng.vertices(), key=functools.cmp_to_key(comparator))
m5 = fillet2d(ng, radius, [vtxs[0], vtxs[3], vtxs[4]])
m5 = fillet2d(m5, radius2, [vtxs[1], vtxs[2], vtxs[5]])

display(m1)
display(m2.right(30))
display(m3.right(60))
display(m4.right(90))
display(m5.right(120))

show()
