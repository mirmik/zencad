#!/usr/bin/env python3
"""
ZenCad API example: textshape
date: 04.10.2019
"""

import os
from zencad import *

zencad_example_directory = os.path.dirname(os.path.realpath(__file__))

testfont = os.path.join(zencad_example_directory, "../fonts/testfont.ttf")
mandarinc = os.path.join(zencad_example_directory, "../fonts/mandarinc.ttf")

m0 = textshape(text="ZenCad", fontpath=testfont, size=100)
m1 = textshape(text="ZenCad", fontpath=mandarinc, size=100)

disp(m0, color.white)
disp(m0.rotateX(deg(90)).translate(0, 70, 0))

disp(m1.translate( 0, 200,  0), color.green)
disp(m1.rotateX(deg(90)).translate( 0, 270, 0), color.yellow)

#find the geometric center of the textshape
m1center = m1.center()
m2 = (
	box(400, 100, 50) 
	- m1.extrude(25).up(25).translate(200 - m1center.x, 50 - m1center.y, 0)
)

disp(m2.forw(400))


show()
