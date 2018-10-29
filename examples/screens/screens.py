#! /usr/bin/env python3
#coding: utf-8


from zencad import *

screen(model=box(10,20,30), path="box.png")

screen(model=cylinder(r=20, h=10), path="cylinder.png")
screen(model=cylinder(r=20, h=10, angle=deg(50)), path="cylinder_sector.png")

screen(model=cone(r1=40, r2=20, h=10), path="cone.png")