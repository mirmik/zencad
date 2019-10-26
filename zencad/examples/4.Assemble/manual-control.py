#!/usr/bin/env python3 
"""
ZenCad example: manual-control

We can control current object position in real time.
In that example we create special widget to change link`s positions by sliders.
"""

from zencad import *
import zencad.assemble
import zencad.cynematic

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

CTRWIDGET = None
SLDS = None

class Slider(QSlider):
	def __init__(self):
		super().__init__(Qt.Horizontal)
		self.setRange(0,10000)
		self.setValue(5000)
		self.setSingleStep(1)


class link(zencad.assemble.unit):
	def __init__(self, h=40, ax=(0,1,0)):
		super().__init__()
		self.set_shape(cylinder(5,h))
		self.rotator = zencad.cynematic.rotator(parent=self, ax=ax, location=up(h))

a = link(ax=(0,1,0))
b = link(ax=(1,0,0))
c = link(ax=(0,1,0))
d = link(ax=(1,0,0))

a.rotator.link(b)
b.rotator.link(c)
c.rotator.link(d)

LINKS = [a,b,c,d]

disp(a)

def preanimate(wdg):
	global CTRWIDGET, SLDS
	CTRWIDGET = QWidget()
	layout = QVBoxLayout()
	SLDS = [ Slider() for i in range(len(LINKS) - 1) ]

	for sld in SLDS:
		layout.addWidget(sld)
	
	CTRWIDGET.setLayout(layout)
	CTRWIDGET.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.Dialog)
	CTRWIDGET.show()

def animate(wdg):
	for i in range(len(LINKS) - 1):
		LINKS[i].rotator.set_coord((SLDS[i].value() - 5000) / 10000 * math.pi * 2)
	a.location_update()

show(animate=animate, preanimate=preanimate)