#!/usr/bin/env python3

# ZenCad Example: SimpleAssemble.py

from zencad import *
import time
import zencad.assemble

yaw_unit = zencad.assemble.unit()
pitch_unit = zencad.assemble.unit(parent=yaw_unit)
roll_unit = zencad.assemble.unit(parent=pitch_unit)
model_unit = zencad.assemble.unit(
	parent=roll_unit,
	parts=[box(20,10,5,center=True) + box(10,20,5,center=True)])

yaw_unit.add_triedron(length=25, arrlen=2)
pitch_unit.add_triedron(length=20, arrlen=2)
roll_unit.add_triedron(length=15, arrlen=2)

# Display ROOT unit
disp(yaw_unit)

T = 4
W = deg(60)
starttime = time.time()
def animate(wdg):
	fromstart = time.time() - starttime

	if fromstart < T:
		yaw_unit.relocate(rotateZ(fromstart / T * W), deep=True)
	elif fromstart < 2*T:
		pitch_unit.relocate(rotateY((fromstart - T) / T * W), deep=True)
	elif fromstart < 3*T:
		roll_unit.relocate(rotateX((fromstart - 2*T) / T * W), deep=True)


show(animate = animate)