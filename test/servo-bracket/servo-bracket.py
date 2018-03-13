#!/usr/bin/env python3
#coding: utf-8

import sys
sys.path.insert(0, "../..")

import zencad.solid as solid
from zencad.widget import *


ear_width = 5
ear_length = 23

servo_x = 40.5 + 2
servo_y = 20 + 2
servo_z = 29 + 2

servo_holes_width = 10
servo_hole_rad = 4.1 / 2.

h_central = 4
h_side = 1.8
h_radius = 7

thickness = 2

bot_holes_offset = 14

def servo_box(x, y, z, t):
	return (solid.box(x+2*t, y+t, z+t) - solid.box(x,y,z).translate(t,0,t))

base = servo_box(servo_x, servo_y, servo_z, thickness)

display(base)

show()