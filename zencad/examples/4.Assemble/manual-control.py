#!/usr/bin/env python3 
"""
ZenCad example: manual-control

We can control current object position in real time.
In that example we create special widget to change link`s positions by sliders.
"""

from zencad import *
import zencad.assemble

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
	def __init__(self, h=40, axis=(0,1,0)):
		super().__init__()
		self.add_shape(cylinder(5,h) + cylinder(6,10,center=True).transform(up(h) * short_rotate((0,0,1), axis)))
		self.rotator = zencad.assemble.rotator(parent=self, axis=axis, location=up(h))

a = link(axis=(0,1,0))
b = link(axis=(1,0,0))
c = link(axis=(0,1,0))
d = link(axis=(1,0,0))

a.rotator.link(b)
b.rotator.link(c)
c.rotator.link(d)
d.rotator.output.add_shape(cone(5,12,40).up(10) + cylinder(5,10))

LINKS = [a,b,c,d]

disp(a)

def preanimate(widget, animate_thread):
	global CTRWIDGET, SLDS
	CTRWIDGET = QWidget()
	layout = QVBoxLayout()
	SLDS = [ Slider() for i in range(len(LINKS)) ]

	for sld in SLDS:
		layout.addWidget(sld)
	
	CTRWIDGET.setLayout(layout)
	CTRWIDGET.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.Dialog)
	CTRWIDGET.show()

def animate(wdg):
	for i in range(len(LINKS)):
		LINKS[i].rotator.set_coord((SLDS[i].value() - 5000) / 10000 * math.pi * 2)
	a.location_update()

def close_handle():
	CTRWIDGET.close()

show(animate=animate, preanimate=preanimate, close_handle=close_handle)