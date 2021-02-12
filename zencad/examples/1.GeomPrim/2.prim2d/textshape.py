#!/usr/bin/env python3
"""
ZenCad API example: textshape
date: 04.10.2019
"""

import os
from zencad import *

zencad_example_directory = zencad.moduledir + "/examples"

testfont = os.path.join(zencad_example_directory, "fonts/testfont.ttf")
mandarinc = os.path.join(zencad_example_directory, "fonts/mandarinc.ttf")

register_font(testfont)
register_font(mandarinc)

m0 = textshape(text="ZenCad", fontname="Ubuntu Mono", size=100)
m1 = textshape(text="ZenCad", fontname="Mandarinc", size=100)

disp(m0, color.white)
disp(m0.rotateX(deg(90)).translate(0, 70, 0))

disp(m1.translate( 0, 200,  0), color.green)
disp(m1.rotateX(deg(90)).translate( 0, 270, 0), color.yellow)

#########################Advanced Example########################################
x = 400
y = 100
z = 50
deep = 10

#find the geometric center of the textshape
m1center = m1.center()
m2 = (
	box(x, y, z) 
	- m1.extrude(deep).up(z-deep).translate(x/2 - m1center.x, y/2 - m1center.y, 0)
)

disp(m2.forw(400))
################################################################################

show()
