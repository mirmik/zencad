#!/usr/bin/env python3
#coding: utf-8

from zencad import *
import evalcache

print(evalcache.__version__)


base = box(100,100,100,center=True)

f1 = ngon(r = 35, n = 3).down(50)
f2 = ngon(r = 35, n = 5).rotateY(deg(90)).left(50)
f3 = circle(35).rotateX(deg(90)).back(50)

s1 = linear_extrude(f1, (0,0,100))
s2 = linear_extrude(f2, (100,0,0))
s3 = linear_extrude(f3, (0,100,0))

m1 = base - s1 - s2 - s3
m2 = base ^ s1 ^ s2 ^ s3
m3 = s1 + s2 + s3

ystep = 200
xstep = 200

display(base.forw(ystep))

display(s1)
display(s2.left(xstep))
display(s3.right(xstep))

display(m1.back(ystep))
display(m2.left(xstep).back(ystep))
display(m3.right(xstep).back(ystep))

show()