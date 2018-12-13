#!/usr/bin/env python3
#coding: utf-8

import math
from zencad import *

m1 = box(10).right(30)
m2 = box(10)
m3 = sphere(10)

scn = Scene()
controller_1 = scn.add(m1.unlazy())
controller_2 = scn.add(m2.unlazy())
controller_3 = scn.add(m3.unlazy())

i = 0
r = 10
def updater_function():
	global i
	i += 1
	if i > 360:
		i = 0

	controller_1.set_location(rotateZ(deg(i)).unlazy())
	controller_2.set_location(translate(0,r*math.sin(deg(i)),0).unlazy())
	controller_3.set_location(translate(0,0,r*math.sin(deg(i))).unlazy())

show(scn, updater_function)

#display(m)
#show()