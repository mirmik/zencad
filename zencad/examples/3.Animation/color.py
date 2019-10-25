#!/usr/bin/env python3
"""
ZenCad API example: Color object animation.
last update: 13.10.2019
"""

from zencad import *
import random

s = box(10, center=True)
controller = disp(s)

clr = color.white
def animate(wdg):
	global clr

	def change(old):
		new = old + random.uniform(-0.1, 0.1)
		if new > 1 or new < 0:
			return old
		return new

	clr = color(change(clr.r), change(clr.g), change(clr.b ))
	controller.set_color(clr)

show(animate=animate)
