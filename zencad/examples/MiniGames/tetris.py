#!/usr/bin/env python3

from zencad import *
import threading
import time
import random

w, h = 20, 20
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

	def can_fall(self):
		print("can_fall")
		for p in self.indexes:
			coords = (p[0] + self.curcoord[0], p[1] + self.curcoord[1] - 1)
			print(coords)
			if coords[1] < 0 or FIELDS[coords[1]][coords[0]].type == 2:
				return False

		return True

	def keep(self):
		for p in self.indexes:
			coords = (p[0] + self.curcoord[0], p[1] + self.curcoord[1])
			FIELDS[coords[1]][coords[0]].type = 2

class Field:
	def __init__(self, i, j):
		self.shp = box(sz, center=True)
		self.shp = self.shp.translate(-w*sz/2+sz/2,0,-h*sz/2+sz/2).translate(sz*j,0,sz*i)
		self.coords = i, j
		self.cube = disp(self.shp)
		self.cube.hide(True)
		self.type = 0

for i in range(h):
	FIELDS.append([])
	for j in range(w):
		FIELDS[-1].append(Field(i,j))

def make_falled_body():
	choices = [
		([(0,0), (1,0), (2,0), (3,0)], zencad.color.green),
		([(0,0), (1,0), (2,0)], zencad.color.blue),
		([(0,0), (1,0), (1,1)], zencad.color.yellow),
	]
	tpl = random.choice(choices)
	return FalledBody(*tpl)

def redraw():
	zencad.gui.application.DISPLAY_WIDGET.view.redraw()

falled_body = None
def timer_loop(wdg):
	global falled_body

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
				
		#redraw()

def animate_settings(wdg, animate_thread):
	animate_thread.set_animate_step(0.75)


#thr = threading.Thread(target=timer_loop)
#thr.start()

disp(body)
show(animate=timer_loop, preanimate=animate_settings)