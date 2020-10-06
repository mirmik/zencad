#!/usr/bin/env python3
#coding: utf-8

from tempfile import mkstemp
from zencad import *
lazy.fastdo = True

m0 = \
(
	zencad.rectangle(10,20) 
	+ zencad.rectangle(10,20,center=True)
	+ zencad.ellipse(10,8)
	-zencad.circle(5)
)

svg = to_svg_string(m0)
m1 = from_svg_string(svg)

fd, path = mkstemp()
to_svg(m0, path)
m2 = from_svg(path)

disp(m0)
disp(m1.right(25))
disp(m2.right(50))

###

m3 = box(20, center=True) - torus(7,3) - torus(7,3).rotX(deg(90)) + box(10, center=True).up(15)
m3 = m3.rotateX(deg(70)).rotateY(deg(30))
m4 = m3 ^ infplane()

hl(m3.move(0,45))
disp(m4.move(0,45))
disp(m4.move(35,45)) 

# BSPLINE : TODO
#svg = to_svg_string(m4)
#m5 = from_svg_string(svg)

#disp(m5.move(70,45)) 

show()
