#!/usr/bin/env python3
#coding: utf-8

from zencad import *
lazy.diag=True

box = box(200, 200, 200, center = True)
sphere1 = sphere(120)
sphere2 = sphere(60)

union = box - sphere1 + sphere2

display(union)

fontpath = os.path.join(os.path.dirname(os.path.realpath(__file__)), "fonts/mandarinc.ttf")
display(textshape("Mirmik", fontpath ,size=100))
show()