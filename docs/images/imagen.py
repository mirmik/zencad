#! /usr/bin/env python3
#coding: utf-8

from zencad import *

wsize = (400, 300)

screen(model=box(10,20,30), path="box.png", size=wsize)
screen(model=sphere(r=10), path="sphere.png", size=wsize)
screen(model=cylinder(r=10, h=20), path="cylinder.png", size=wsize)

screen(model=cone(r1=20, r2=10, h=20), path="cone.png", size=wsize)
screen(model=cylinder(r=10, h=20, angle=deg(50)), path="cylinder_sector.png", size=wsize)
screen(model=torus(r1=20, r2=5), path="torus.png", size=wsize)
