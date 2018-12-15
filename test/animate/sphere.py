#!/usr/bin/env python3
#coding: utf-8

import math
from zencad import *

m1 = box(10).right(30)
m2 = box(10)
m3 = sphere(10)

scn = Scene()
controller_1 = scn.add(m1.unlazy())
controller_11 = scn.add(m1.unlazy().right(30))
controller_12 = scn.add(m1.unlazy().right(60))
controller_13 = scn.add(m1.unlazy().right(90))
controller_14 = scn.add(m1.unlazy().right(120))
controller_15 = scn.add(m1.unlazy().right(150))
controller_16 = scn.add(m1.unlazy().right(180))
controller_17 = scn.add(m1.unlazy().right(210))
controller_18 = scn.add(m1.unlazy().right(240))
controller_2 = scn.add(m2.unlazy())
controller_21 = scn.add(m2.unlazy())
controller_22 = scn.add(m2.unlazy())
controller_23 = scn.add(m2.unlazy())
controller_24 = scn.add(m2.unlazy())
controller_25 = scn.add(m2.unlazy())
controller_26 = scn.add(m2.unlazy())
controller_27 = scn.add(m2.unlazy())
controller_3 = scn.add(m3.unlazy())
controller_3 = scn.add(m3.unlazy())
controller_4 = scn.add(m3.unlazy())
controller_5 = scn.add(m3.unlazy())
controller_6 = scn.add(m3.unlazy())
controller_7 = scn.add(m3.unlazy())
controller_8 = scn.add(m3.unlazy())
controller_9 = scn.add(m3.unlazy())

i = 0
r = 50
def updater_function(viewer):
	global i
	i += 1
	if i > 360:
		i = 0

	controller_1.set_location(rotateZ(deg(i)).unlazy())
	controller_11.set_location(rotateZ(deg(i)).unlazy())
	controller_12.set_location(rotateZ(deg(i)).unlazy())
	controller_13.set_location(rotateZ(deg(i)).unlazy())
	controller_14.set_location(rotateZ(deg(i)).unlazy())
	controller_15.set_location(rotateZ(deg(i)).unlazy())
	controller_16.set_location(rotateZ(deg(i)).unlazy())
	controller_17.set_location(rotateZ(deg(i)).unlazy())
	controller_18.set_location(rotateZ(deg(i)).unlazy())
	controller_2.set_location(translate(0,r*math.sin(deg(i)),0).unlazy())
	controller_21.set_location(translate(0,r*2*math.sin(deg(i)),0).unlazy())
	controller_22.set_location(translate(0,r*3*math.sin(deg(i)),0).unlazy())
	controller_23.set_location(translate(0,r*4*math.sin(deg(i)),0).unlazy())
	controller_24.set_location(translate(0,r*5*math.sin(deg(i)),0).unlazy())
	controller_25.set_location(translate(0,r*6*math.sin(deg(i)),0).unlazy())
	controller_26.set_location(translate(0,r*7*math.sin(deg(i)),0).unlazy())
	controller_27.set_location(translate(0,r*8*math.sin(deg(i)),0).unlazy())
	controller_3.set_location(translate(0,0,r*math.sin(deg(i))).unlazy())
	controller_4.set_location(translate(0,0,r*2*math.sin(deg(i))).unlazy())
	controller_5.set_location(translate(0,0,r*3*math.sin(deg(i))).unlazy())
	controller_6.set_location(translate(0,0,r*4*math.sin(deg(i))).unlazy())
	controller_7.set_location(translate(0,0,r*5*math.sin(deg(i))).unlazy())
	controller_8.set_location(translate(0,0,r*6*math.sin(deg(i))).unlazy())
	controller_9.set_location(translate(0,0,r*7*math.sin(deg(i))).unlazy())

	viewer.redraw()

show(scn, updater_function)

#display(m)
#show()