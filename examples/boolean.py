#!/usr/bin/env python3
#coding: utf-8

from zencad import *
lazy.diag = True

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

#font = "/usr/share/fonts/truetype/ubuntu/UbuntuMono-R.ttf"

#t1 = textshape("difference", font, 40)
#t1c = t1.center()
#t1=t1.translate(-t1c.x, -t1c.y, 0).rotateZ(deg(45))
#
#t2 = textshape("intersect", font, 40)
#t2c = t2.center()
#t2=t2.translate(-t2c.x, -t2c.y, 0).rotateZ(deg(45))
#
#t3 = textshape("union", font, 40)
#t3c = t3.center()
#t3=t3.translate(-t3c.x, -t3c.y, 0).rotateZ(deg(45))

display(base.forw(ystep))

display(s1)
display(s2.left(xstep))
display(s3.right(xstep))

display(m1.back(ystep))
display(m2.left(xstep).back(ystep))
display(m3.right(xstep).back(ystep))

display(m1.back(ystep))
display(m2.left(xstep).back(ystep))
display(m3.right(xstep).back(ystep))

#display(t1.back(ystep).up(70))
#display(t2.left(xstep).back(ystep).up(70))
#display(t3.right(xstep).back(ystep).up(70))

show()