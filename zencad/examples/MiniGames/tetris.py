#!/usr/bin/env python3

from zencad import *
import threading
import time
import random
import types

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

import threading

w, h = 10, 20
sz = 10
FIELDS=[]

body = box(sz*w+2*sz, sz, sz*h+2*sz, center=True) - box(sz*w, sz, sz*h, center=True) 

class FalledBody:
	def __init__(self, indexes, color):
		self.indexes = indexes
		self.color = color
		self.curcoord = (w//2, h - self.get_height())

	def get_height(self):
		maxh = 0
		for p in self.indexes:
			if p[1] > maxh: maxh = p[1]
		return maxh + 1

	def draw(self):
		for p in self.indexes:
			coords = (p[0] + self.curcoord[0], p[1] + self.curcoord[1])
			FIELDS[coords[1]][coords[0]].cube.set_color(self.color)
			FIELDS[coords[1]][coords[0]].cube.hide(False)
			FIELDS[coords[1]][coords[0]].type = 1

	def hide(self):	
		for p in self.indexes:
			coords = (p[0] + self.curcoord[0], p[1] + self.curcoord[1])
			FIELDS[coords[1]][coords[0]].cube.hide(True)
			FIELDS[coords[1]][coords[0]].type = 0

	def fall(self):
		self.curcoord = (self.curcoord[0], self.curcoord[1]-1)

	def check_valid(self, newcoord, indexes):
		for p in indexes:
			coords = (p[0] + newcoord[0], p[1] + newcoord[1])
			if coords[0] < 0 or coords[0] >= w:
				return False
			if coords[1] < 0 or coords[1] >= h:
				return False
			if FIELDS[coords[1]][coords[0]].type == 2:
				return False

		return True


	def can_fall(self):
		for p in self.indexes:
			coords = (p[0] + self.curcoord[0], p[1] + self.curcoord[1] - 1)
			if coords[1] < 0 or FIELDS[coords[1]][coords[0]].type == 2:
				return False

		return True

	def keep(self):
		for p in self.indexes:
			coords = (p[0] + self.curcoord[0], p[1] + self.curcoord[1])
			FIELDS[coords[1]][coords[0]].type = 2

	def up_handle(self):
		newindexes = [ (-ind[1], ind[0]) for ind in self.indexes ]
		valid = self.check_valid(self.curcoord, newindexes)
		if valid:
			self.hide()
			self.indexes = newindexes
			self.draw()

	def down_handle(self):
		validcoord = self.curcoord
		itcoord = self.curcoord
		while self.check_valid(itcoord, self.indexes):
			validcoord = itcoord
			itcoord = (itcoord[0], itcoord[1]-1)
		self.hide()
		self.curcoord = validcoord
		self.draw()
			

	def xmove_handle(self, add):
		newcoord = (self.curcoord[0] + add, self.curcoord[1])
		valid = self.check_valid(newcoord, self.indexes)
		if valid:
			self.hide()
			self.curcoord = newcoord
			self.draw()

	def right_handle(self):
		self.xmove_handle(+1)
	
	def left_handle(self):
		self.xmove_handle(-1)

class Field:
	def __init__(self, i, j):
		self.shp = box(sz, center=True)
		self.shp = self.shp.translate(-w*sz/2+sz/2,0,-h*sz/2+sz/2).translate(sz*j,0,sz*i)
		self.coords = i, j
		self.cube = disp(self.shp)
		self.cube.hide(True)
		self.type = 0

	def copy(self, oth):
		if oth.type == 0:
			self.cube.hide(True)
		else:
			self.cube.hide(False)
			self.cube.set_color(oth.cube.color())

		self.type = oth.type

def clean():
	for i in range(h):
		istype2 = 0
		for j in range(w):
			if FIELDS[i][j].type == 2:
				istype2 +=1
		if istype2 == w:
			for ii in range(i, h-1):
				for j in range(w):
					FIELDS[ii][j].copy(FIELDS[ii+1][j]) 
			
			for j in range(w):
				FIELDS[h-1][j].type = 0	
				FIELDS[h-1][j].cube.hide(True)

for i in range(h):
	FIELDS.append([])
	for j in range(w):
		FIELDS[-1].append(Field(i,j))

def make_falled_body():
	choices = [
		([(0,1), (0,0), (0,-1), (-1,-1)], color.blue),
		([(0,2), (0,1), (0,0), (0,-1)], color.cian),
		([(1,1), (0,1), (1,0), (0,0)], color.yellow),
		([(0,2), (0,1), (0,0), (1,0)], color.orange),
		([(-1,1), (0,1), (0,0), (1,0)], color.red),
		([(-1,0), (0,0), (1,0), (0,1)], color.magenta),
		([(-1,0), (0,0), (0,1), (1,1)], color.green),
		#([(-1,0), (0,0), (1,0), (2,0)], zencad.color.green),
		#([(-1,0), (0,0), (1,0)], zencad.color.blue),
		#([(-1,0), (0,0), (0,1)], zencad.color.yellow),
		#([(-1,0), (0,0), (0,1), (1,1)], zencad.color.red),
		#([(1,0), (0,0), (0,1), (-1,1)], zencad.color.red),
		#([(0,0)], zencad.color.magenta),
		#([(0,0), (0,-1), (0,1), (-1,0), (1,0)], zencad.color.magenta),
		#([(0,0), (0,-1), (-1,0), (1,0)], zencad.color.blue),
	]
	tpl = random.choice(choices)
	return FalledBody(*tpl)

def redraw():
	zencad.gui.application.DISPLAY_WIDGET.view.redraw()

lock = QMutex()
falled_body = None
def timer_loop(wdg):
	global falled_body

	lock.lock()
	if falled_body is None:
		falled_body = make_falled_body()
		falled_body.draw()
	else:			
		if falled_body.can_fall():
			falled_body.hide()
			falled_body.fall()
			falled_body.draw()
		else:
			falled_body.keep()
			falled_body = None

	clean()
	lock.unlock()
				
		#redraw()

def animate_settings(wdg, animate_thread):
	def keyPressEvent(self, ev):
		if falled_body is None:
			return
		lock.lock()
		if ev.key() == Qt.Key_Up: falled_body.up_handle()
		elif ev.key() == Qt.Key_Down: falled_body.down_handle()
		elif ev.key() == Qt.Key_Right: falled_body.right_handle()
		elif ev.key() == Qt.Key_Left: falled_body.left_handle()
		clean()
		wdg.redraw()
		lock.unlock()

	animate_thread.set_animate_step(0.75)
	raw_keyPressEvent = wdg.keyPressEvent
	wdg.keyPressEvent = types.MethodType(keyPressEvent, wdg)


#thr = threading.Thread(target=timer_loop)
#thr.start()

disp(body)
show(animate=timer_loop, preanimate=animate_settings)