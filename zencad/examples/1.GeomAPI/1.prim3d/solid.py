#!/usr/bin/env python3
# coding: utf-8

from zencad import *

zencad.lazy.fastdo = True
zencad.lazy.decache = False

box_a = 10
box_b = 10
box_c = 20

m01 = box(size=box_a)
m02 = box(size=(box_a, box_b, box_c))
m03 = box(box_a, box_b, box_c)
m01c = box(size=box_a, center=True)
m02c = box(size=(box_a, box_b, box_c), center=True)
m03c = box(box_a, box_b, box_c, center=True)

m1 = sphere(5)

tor_r1 = 5
tor_r2 = 2
tor_u = deg(135)
tor_v1 = deg(-90)
tor_v2 = deg(180)
m20 = torus(r1=tor_r1, r2=tor_r2)
m21 = torus(r1=tor_r1, r2=tor_r2, yaw=tor_u)
m22 = torus(r1=tor_r1, r2=tor_r2, pitch=(tor_v1, tor_v2))
m23 = torus(r1=tor_r1, r2=tor_r2, pitch=(tor_v1, tor_v2), yaw=tor_u)

cyl_r = 5
cyl_h = 10
m30 = cylinder(r=cyl_r, h=cyl_h)
m31 = cylinder(r=cyl_r, h=cyl_h, yaw=deg(90))
m30c = cylinder(r=cyl_r, h=cyl_h, center=True)
m31c = cylinder(r=cyl_r, h=cyl_h, yaw=deg(90), center=True)

cone_r1 = 6
cone_r2 = 4
cone_h = 10
m40 = cone(r1=cone_r1, r2=cone_r2, h=cone_h)
m41 = cone(r1=cone_r1, r2=cone_r2, h=cone_h, yaw=deg(90))
m40c = cone(r1=cone_r1, r2=cone_r2, h=cone_h, center=True)
m41c = cone(r1=cone_r1, r2=cone_r2, h=cone_h, yaw=deg(90), center=True)

display(m01)
display(m02.forw(20))
display(m03.forw(40))
display(m01c.forw(60))
display(m02c.forw(80))
display(m03c.forw(100))

display(m1.right(20))

display(m20.right(40))
display(m21.right(40).forw(20))
display(m22.right(40).forw(40))
display(m23.right(40).forw(60))

display(m30.right(60))
display(m31.right(60).forw(20))
display(m30c.right(60).forw(60))
display(m31c.right(60).forw(80))

display(m40.right(80))
display(m41.right(80).forw(20))
display(m40c.right(80).forw(60))
display(m41c.right(80).forw(80))

show()
