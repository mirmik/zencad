#! /usr/bin/env python3
#coding: utf-8

from zencad import *
import os

import zencad.visual

#lazy.diag = True

wsize = (300, 200)

if not os.path.exists("generic"):
    os.makedirs("generic")

def doscreen(model, path, size):
	print("screen (path:{0}, size:{1})".format(path, size))
	screen(model, path, size)
	screen(model, "generic/"+path, size)

doscreen(model=box(10,20,30), path="box.png", size=wsize)
doscreen(model=sphere(r=10), path="sphere.png", size=wsize)
doscreen(model=cylinder(r=10, h=20), path="cylinder.png", size=wsize)

doscreen(model=cone(r1=20, r2=10, h=20), path="cone.png", size=wsize)
doscreen(model=cylinder(r=10, h=20, angle=deg(50)), path="cylinder_sector.png", size=wsize)

doscreen(model=torus(r1=20, r2=5), path="torus.png", size=wsize)
doscreen(model=circle(r=20), path="circle.png", size=wsize)
doscreen(model=ngon(r=20, n=6), path="ngon.png", size=wsize)