#!/usr/bin/env python3 
"""
ZenCad example: manual-control

We can control current object position in real time.
In that example we create special widget to change link`s positions by sliders.
"""

from zencad import *
import zencad.assemble
import zencad.libs.kinematic
import zencad.malgo

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

import time

CTRWIDGET = None
SLDS = None

XSLD = None
YSLD = None
ZSLD = None

class Slider(QSlider):
	def __init__(self):
		super().__init__(Qt.Horizontal)
		self.setRange(-5000,5000)
		self.setValue(0)
		self.setSingleStep(1)


class link(zencad.assemble.unit):
	def __init__(self, h=40, axis=(0,1,0)):
		super().__init__()
		if axis != (0,0,1):
			self.add_shape(cylinder(5,h) + cylinder(6,10,center=True).transform(up(h) * short_rotate((0,0,1), axis)))
		else:
			self.add_shape(cylinder(5,h))	
		self.rotator = zencad.assemble.rotator(parent=self, axis=axis, location=up(h))

r = zencad.assemble.rotator(axis=(0,0,1))
a = link(axis=(0,1,0))
b = link(axis=(1,0,0))
c = link(axis=(0,1,0))
d = link(axis=(1,0,0))
e = link(axis=(0,1,0))

r.link(a)
a.rotator.link(b)
b.rotator.link(c)
c.rotator.link(d)
d.rotator.link(e)

LINKS = [a,b,c,d,e]

chain = zencad.libs.kinematic.kinematic_chain(LINKS[-1].rotator.output)

disp(a)

def preanimate(widget, animate_thread):
	global CTRWIDGET, XSLD, YSLD, ZSLD
	CTRWIDGET = QWidget()
	layout = QVBoxLayout()
	XSLD = Slider()
	YSLD = Slider()
	ZSLD = Slider()

	layout.addWidget(XSLD)
	layout.addWidget(YSLD)
	layout.addWidget(ZSLD)

	CTRWIDGET.setLayout(layout)
	CTRWIDGET.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.Dialog)
	CTRWIDGET.show()

tgtshp = sphere(5)
ctr = disp(tgtshp) 

K = 1
stime = time.time()
lasttime = stime
def animate(wdg):
	global lasttime
	curtime = time.time()
	DELTA = curtime - lasttime
	lasttime = curtime

	target_location = translate(XSLD.value()/5000*120, YSLD.value()/5000*120, ZSLD.value()/5000*120)

	sens = chain.sensivity()
	error = LINKS[-1].rotator.output.global_location.inverse() * target_location

	ttrans = error.translation() * K
	rtrans = error.rotation().rotation_vector() * K 

	target = ttrans
	vcoords, iters = zencad.malgo.svd_backpack(target, vectors=[v for w,v in sens ])

	r.set_coord(r.coord + vcoords[0] * DELTA)
	for i in range(len(LINKS)):
		LINKS[i].rotator.set_coord(LINKS[i].rotator.coord + vcoords[i+1] * DELTA)

	ctr.relocate(target_location)
	a.location_update()

def close_handle():
	CTRWIDGET.close()

show(animate=animate, preanimate=preanimate, close_handle=close_handle)