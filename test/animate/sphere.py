#!/usr/bin/env python3
#coding: utf-8

import math
from zencad import *
test_mode()

m = sphere(10).right(30)

scn = Scene()
controller = scn.add(m.unlazy())

i = 0
r = 10
def updater_function():
	global i
	i += 1
	if i > 360:
		i = 0

	controller.set_location(r*math.sin(deg(i)), r*math.cos(deg(i)), 0)

show(scn, updater_function)

#display(m)
#show()