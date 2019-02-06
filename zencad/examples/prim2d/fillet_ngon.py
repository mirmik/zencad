#!/usr/bin/env python3
#coding: utf-8

from zencad import *
import evalcache
lazy.diag = True 
#test_mode()

ng = ngon(r = 10, n = 6)

#Fillter all vertices
print("m1:")
m1 = ngon(r = 10, n = 6).fillet(3)
m1.unlazy()

#Generator can be used for array filtering
print("m2:")
m2 = ng.fillet(3, [v for v in ng.vertices() if v.x < 0])
m2.unlazy()

#We can use lazy lambda for improve caching algorithm
print("m3:")
m3 = ng.fillet(3, lazy(lambda: [v for v in ng.vertices() if v.y < 0])())
m3.unlazy()

#Each one syntax variant (and inaccuracy of float when comparing)
print("m4:")
m4 = ng.fillet(3, evalcache.select(ng.vertices(), lambda v: abs(v.y) < 0.001))
m4.unlazy()

print("display:")
display(m1)
display(m2.right(30))
display(m3.right(60))
display(m4.right(90))

show()