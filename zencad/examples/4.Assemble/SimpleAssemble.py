#!/usr/bin/env python3

# ZenCad Example: SimpleAssemble.py

from zencad import *
import time
import zencad.assemble

a=10
b=10

# Make base
unit1_shape = box(a, center=True) + cylinder(r=3,h=b).up(a/2)
unit1 = zencad.assemble.unit()
unit1.add_shape(unit1_shape)
unit1.relocate(translate(0,0,a/2))

# Make links
link0 = zencad.assemble.unit(parent=unit1, location=translate( a/2, a/2, a/2) * rotate((-1, 1, 0), deg(45)))
link1 = zencad.assemble.unit(parent=unit1, location=translate(-a/2, a/2, a/2) * rotate((-1,-1, 0), deg(45)))
link2 = zencad.assemble.unit(parent=unit1, location=translate( a/2,-a/2, a/2) * rotate(( 1, 1, 0), deg(45)))
link3 = zencad.assemble.unit(parent=unit1, location=translate(-a/2,-a/2, a/2) * rotate(( 1,-1, 0), deg(45)))
toplink = zencad.assemble.unit(parent=unit1, location=translate(0,0,a/2+b))
toplink2 = zencad.assemble.unit(parent=toplink)

# Draw triedron for links
for link in (link0, link1, link2, link3):
	link.add_triedron(length=5, arrlen=1)

# Draw triedron for toplinks
toplink.add_triedron(length=10, arrlen=1)
toplink2.add_triedron(length=5, arrlen=1)

unit2 = zencad.assemble.unit()
unit2.add_shape(cylinder(r=3, h=3))

unit3 = zencad.assemble.unit()
unit3.add_shape(cone(r1=3, r2=2, h=3))

unit4 = zencad.assemble.unit()
unit4.add_shape(box(2, center=True).up(1))

link1.link(unit2)
link2.link(unit3)
toplink2.link(unit4)

disp(unit1)

def animate(self):
	toplink2.relocate(rotateZ(time.time()), deep=True)

show(animate = animate)