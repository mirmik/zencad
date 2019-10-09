#!/usr/bin/env python3

from zencad import *
import zencad.libs.rigidity
from zencad.libs.screw import screw

import numpy

N = 20
l = 200
s = l / N

gravity_mass = screw(ang=(0,0,0), lin=(0,0,-10))

class rigidity_test_element(zencad.assemble.unit):
	def __init__(self):
		E = 200*10**2
		G = 200*10**2
		F = 1
		Jx = 1
		Jy = 1
		Jz = 1
		
		h=s
		r=5

		self.con = moveX(s)

		super().__init__()
		self.shp = cylinder(r, h).rotateY(deg(90))
		self.set_shape(self.shp)
		self.connector = zencad.assemble.unit(parent=self, location=self.con)

		self.rigidity_model = zencad.libs.rigidity.rod_finite_element_model(E, G, F, Jx, Jy, Jz, h)

		self.force_model = zencad.libs.rigidity.force_model(inunit=self, outunit=self.connector)

els = []
for i in range(N):
	a = rigidity_test_element()
	if i != 0:
		els[-1].connector.link(a)
	els.append(a)

#els[0].relocate(rotateY(-deg(90)))

els[0].location_update()

for i in range(1):

#	els[-1].force_model.output_force = gravity_mass

#	for i, d in enumerated(reversed(els)):
#		d.force_model.evaluate_input_force()
#		els
		
#		force_screw = d.force_model.output_force.inverse_transform(d.global_location)
#		print(force_screw)

	for d in els:
		force_screw = gravity_mass
		rid = d.rigidity_model.eval_deflection(force_screw)
		print(rid)

		d.connector.relocate(translate(rid.lin) * rotate(rid.ang.normalize(), numpy.linalg.norm(rid.ang)) * d.con)
		#print(rid)
	
	els[0].location_update()

disp(els[0])
zencad.show()