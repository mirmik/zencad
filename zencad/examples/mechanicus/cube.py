#!/usr/bin/env python3

import numpy as np
import matplotlib.pyplot as plt
import sys
from skimage import measure, io
from itertools import chain

import math
import zencad

zencad.lazy.diag = True

from zencad import *
import mech

mechanicus, base = mech.buildpair()

cube = box(1000, center=True)

mech = [display(mechanicus, zencad.Color(1,1,1)) for i in range(0,6)]
base = [display(base, zencad.Color(0.2,0.2,0.2)) for i in range(0,6)]

i = 0
def animate(wdg):
	global i
	i += 0.01
	trans = rotateZ(i) * translate(0,0,500)
	mech[0].set_location(trans)
	base[0].set_location(trans)
	mech[1].set_location(rotateX(deg(180)) * trans)
	base[1].set_location(rotateX(deg(180)) * trans)
	mech[2].set_location(rotateX(deg(90)) * trans)
	base[2].set_location(rotateX(deg(90)) * trans)
	mech[3].set_location(rotateX(deg(90)) * rotateX(deg(180)) * trans)
	base[3].set_location(rotateX(deg(90)) * rotateX(deg(180)) * trans)
	mech[4].set_location(rotateY(deg(90)) * trans)
	base[4].set_location(rotateY(deg(90)) * trans)
	mech[5].set_location(rotateY(deg(90)) * rotateX(deg(180)) * trans)
	base[5].set_location(rotateY(deg(90)) * rotateX(deg(180)) * trans)
	wdg.view.redraw()

display(cube, Color(0.3, 0.2, 0.2))
show(animate = animate)

#scn = Scene()
#mech = [scn.add(mechanicus.unlazy(), zencad.Color(1,1,1)) for i in range(0,6)]
#base = [scn.add(base.unlazy(), zencad.Color(0.2,0.2,0.2)) for i in range(0,6)]
#scn.add(cube.unlazy(), Color(0.3, 0.2, 0.2))
#
#viewer = Viewer(scn)
#view = viewer.create_view()
#view.set_virtual_window(800, 600)
#view.fit_all()
#
#zencad.shower.disable_lazy()
#
#pp = 0
#for i in range(0, 10240):
#	print("do screen", i)
#	pp += 0.01
#	trans1 = rotateZ(pp/2) * translate(0,0,500)
#	trans2 = rotateZ(pp*2) * translate(0,0,500)
#	trans3 = rotateZ(pp*3) * translate(0,0,500)
#	trans4 = rotateZ(pp) * translate(0,0,500)
#	trans5 = rotateZ(pp/3) * translate(0,0,500)
#	trans6 = rotateZ(pp*4) * translate(0,0,500)
#	mech[0].set_location(trans1)
#	base[0].set_location(trans1)
#	mech[1].set_location(rotateX(deg(180)) * trans2)
#	base[1].set_location(rotateX(deg(180)) * trans2)
#	mech[2].set_location(rotateX(deg(90)) * trans3)
#	base[2].set_location(rotateX(deg(90)) * trans3)
#	mech[3].set_location(rotateX(deg(90)) * rotateX(deg(180)) * trans4)
#	base[3].set_location(rotateX(deg(90)) * rotateX(deg(180)) * trans4)
#	mech[4].set_location(rotateY(deg(90)) * trans5)
#	base[4].set_location(rotateY(deg(90)) * trans5)
#	mech[5].set_location(rotateY(deg(90)) * rotateX(deg(180)) * trans6)
#	base[5].set_location(rotateY(deg(90)) * rotateX(deg(180)) * trans6)
#	view.set_eye(zencad.rotateZ(zencad.deg(-0.8))(view.eye()))
#	zencad.visual.screen_view(view, "screens/an{}.jpg".format(i), (800,600))
#

scn = Scene()
mech = [scn.add(mechanicus.unlazy(), zencad.Color(1,1,1)) for i in range(0,6)]
base = [scn.add(base.unlazy(), zencad.Color(0.2,0.2,0.2)) for i in range(0,6)]
scn.add(cube.unlazy(), Color(0.3, 0.2, 0.2))

