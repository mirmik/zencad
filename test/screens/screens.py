#! /usr/bin/env python3
#coding: utf-8


from zencad import *

screen(model=box(10,20,30), path="box.png")
screen(model=sphere(r=10), path="sphere.png")
screen(model=cylinder(r=10, h=20), path="cylinder.png")

screen(model=cone(r1=20, r2=10, h=20), path="cone.png")
screen(model=cylinder(r=10, h=20, angle=deg(50)), path="cylinder_sector.png")
screen(model=torus(r1=20, r2=5), path="torus.png")
