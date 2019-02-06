#!/usr/bin/env python3
#coding: utf-8

from zencad import *
import evalcache
import functools
lazy.diag = True 

ng = ngon(r = 10, n = 6)
radius = 4
radius2 = 8

print("***Start example***")
print("vertices:")
print(ng.vertices().unlazy())

# Fillter all vertices
print("m1:")
m1 = ngon(r = 10, n = 6).fillet(radius)
m1.unlazy()

# Generator can be used for array filtering
print("m2:")
m2 = ng.fillet(radius, [v for v in ng.vertices() if v.x < 0])
m2.unlazy()

# We can use lazy lambda for improve caching algorithm
print("m3:")
m3 = ng.fillet(radius, lazy(lambda: [v for v in ng.vertices() if v.y < 0])())
m3.unlazy()

# One more syntax variant (and inaccuracy of float when comparing)
print("m4:")
m4 = ng.fillet(radius, evalcache.select(ng.vertices(), lambda v: abs(v.y) < 0.001))
m4.unlazy()

# Advanced version with indexing of sorted array of points
print("m5:")
def comparator(a,b):
	"""sort by yx_order"""
	xdiff = a.x - b.x
	ydiff = a.y - b.y

	if abs(ydiff) > 0.001: return ydiff
	if abs(xdiff) > 0.001: return xdiff

	return 0

vtxs = sorted(ng.vertices(), key=functools.cmp_to_key(comparator))
m5 = fillet(ng, radius, [vtxs[0], vtxs[3], vtxs[4]])
m5 = fillet(m5, radius2, [vtxs[1], vtxs[2], vtxs[5]])

print("display:")
display(m1)
display(m2.right(30))
display(m3.right(60))
display(m4.right(90))
display(m5.right(120))

show()