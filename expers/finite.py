#!/usr/bin/env python3

from zencad import *
import zencad.malgo
import zencad.cynematic
import zencad.libs.rigidity
from zencad.libs.screw import screw

import time
import numpy

gravity_mass = screw(ang=(0,0,0), lin=(0,0,-10))

class finite_element(zencad.assemble.unit):
	def __init__(self, h):
		super().__init__()

		#E = 200000 * 10**6
		#G = 82 * 10**9
		E = 100 * 10**6
		G = 82 * 10**9
		
		F = 1
		Jx = 1
		Jy = 1
		Jz = 1

		r=5

		self.con = moveX(h)

		self.shp = cylinder(r, h).rotateY(deg(90))
		self.set_shape(self.shp)
		self.connector = zencad.assemble.unit(parent=self, location=self.con)

		self.flexibility_model = zencad.libs.rigidity.rod_flexibility_matrix(E, G, F, Jx, Jy, Jz, h)
#		self.rigidity_model = zencad.libs.rigidity.rod_finite_element_model(E, G, F, Jx, Jy, Jz, h)

		#self.force_model = zencad.libs.rigidity.force_model(inunit=self, outunit=self.connector)

class rod:
	def __init__(self, l, N):
		self.els = []
		for i in range(N):
			a = finite_element(l/N)
			if i != 0:
				self.els[-1].connector.link(a)
			self.els.append(a)

		self.rotator = zencad.cynematic.rotator(parent=self.els[-1].connector, ax=(0,1,0))

		self.input = self.els[0]
		self.output = self.rotator

class mass(zencad.assemble.unit):
	def __init__(self):
		super().__init__()
		self.set_shape(box(12, center=True))
		self.force_model = zencad.libs.rigidity.force_model_mass_point(self, 20, vec=(-1,0,1))

r0 = rod(200, 20)
mass = mass()
r0.output.link(mass)

base = zencad.assemble.unit()
base.link(r0.input)

base.relocate(rotateZ(deg(90)))
base.location_update()



fmodel = zencad.libs.rigidity.force_model_algorithm(r0.input)
fmodel.attach()

t = time.time()

for i in range(5):
	fmodel.force_evaluation()
	fmodel.deformation_evaluation()
	fmodel.apply_deformation()

r0.input.location_update()

print(mass.global_location)
