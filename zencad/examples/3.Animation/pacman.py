#!/usr/bin/env python3
# coding: utf-8

from zencad import *
import zencad.assemble
import time

class Pacman(zencad.assemble.unit):
	def __init__(self):
		super().__init__()
		self.rot0 = zencad.assemble.rotator(axis=(0,1,0), parent=self)
		self.rot1 = zencad.assemble.rotator(axis=(0,1,0), parent=self)

		self.part0 = zencad.assemble.unit()
		self.part1 = zencad.assemble.unit()

		angle = deg(180)
		upper = (sphere(r=30, yaw=angle)
			- sphere(r=10).move(-25, 20, 15)
			- sphere(r=10).move(-25, 20, -15)
		) 
		self.part0.add_shape(upper.rotateZ(0).rotateX(deg(90)), color.yellow)
		self.part0.add_shape(sphere(3).move(-20,12,15), color.green)
		self.part0.add_shape(sphere(3).move(-20,-12,15), color.blue)
		self.part1.add_shape(sphere(r=30, yaw=angle).rotateZ(-angle).rotateX(deg(90)), color.yellow)

		self.rot0.link(self.part0)
		self.rot1.link(self.part1)

pacman = Pacman()
pacman.rot0.set_coord(deg(30))
pacman.rot1.set_coord(-deg(30))

disp(pacman)

R = 30
N = 4

sph0 = disp(sphere(r=3))
sph1 = disp(sphere(r=3))
sph2 = disp(sphere(r=3))
sph3 = disp(sphere(r=3))

sph0.relocate(move(-R))
sph1.relocate(move(-R*2))
sph2.relocate(move(-R*3))
sph3.relocate(move(-R*4))

spharr = [sph0,sph1,sph2,sph3]

lastiter = 0
start_time = time.time()
def animate(wdg):
	global lastiter
	t = time.time() - start_time
	t = t + 0

	T=1
	if t > T*4*2:
		return

	iteration = int((t + T) / (2*T))
	if lastiter != iteration:
		spharr[lastiter].hide(True)
	lastiter = iteration

	lt = t - int(t / (2*T)) * 2*T

	if 0 < lt < T:
		pacman.rot0.set_coord(deg(30) * (T - lt))
		pacman.rot1.set_coord(-deg(30) * (T - lt))

	if T < lt < 2*T:
		pacman.rot0.set_coord(deg(30) * (lt-T))
		pacman.rot1.set_coord(-deg(30) * (lt-T))

	pacman.relocate(translate(-t*R/T/2,0,0))
	pacman.location_update()
	

show(animate=animate)
