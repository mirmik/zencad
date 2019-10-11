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

		self.force_model = zencad.libs.rigidity.force_model_mass_point(self, 0.5)
		self.rotator = zencad.cynematic.rotator(parent=self.els[-1].connector, ax=(0,1,0))

		self.input = self.els[0]
		self.output = self.rotator


class mass(zencad.assemble.unit):
	def __init__(self):
		super().__init__()
		self.set_shape(box(12, center=True))
		self.force_model = zencad.libs.rigidity.force_model_mass_point(self, 20)

r0 = rod(200, 20)
r1 = rod(200, 20)
r2 = rod(200, 20)

mass = mass()
rot = zencad.cynematic.rotator(ax=(0,1,0))
rot.link(r0.input)
r0.output.link(r1.input)
r1.output.link(r2.input)
r2.output.link(mass)

rot.set_coord(0)
r0.output.set_coord(deg(-20))
r1.output.set_coord(deg(20))
r2.output.set_coord(deg(-20))

#els[0].relocate(rotateY(-deg(90)))

#zencad.libs.rigidity.attach_force_model(els[0])
base = rot
base.location_update()

fmodel = zencad.libs.rigidity.force_model_algorithm(base)
fmodel.attach()

#els[-1].force_model.output_force = zencad.libs.screw.screw((0,0,0), (0,0,-10))

#fmodel.
#fmodel.

t = time.time()
for i in range(5):
	fmodel.force_evaluation()
	fmodel.deformation_evaluation()
	fmodel.apply_deformation()


#while True:

base.location_update()
disp(base)

tmodel = mass.global_location

lasttime = time.time()
chain = zencad.cynematic.cynematic_chain(mass)
iteration = 0
def animate(wdg):
	global tmodel
	global lasttime
	global iteration

	curtime = time.time()
	deltatime = curtime - lasttime
	lasttime = curtime

	iteration += 1
	if iteration < 10:
		return

	fmodel.force_evaluation()
	fmodel.deformation_evaluation()
	fmodel.apply_deformation()

	senses = chain.sensivity()

	DELTATIME = deltatime
	TSPD = 40
	K = 10

	tspd = numpy.array([-TSPD,0,0])
	tmodel = pyservoce.translate(*(tspd * DELTATIME)) * tmodel
	current = mass.global_location	

	ftrans = current.inverse() * tmodel
	ttrans = ftrans.translation() * K
	rtrans = ftrans.rotation().rotation_vector() * K 
	target = (*rtrans,*ttrans + current.inverse()(pyservoce.vector3(*tspd)))

	vcoords, iters = zencad.malgo.svd_backpack(target, 
		vectors=[(*w, *v) for w, v in senses])

	rot.set_coord(r0.output.coord + vcoords[0] * DELTATIME)
	r0.output.set_coord(r0.output.coord + vcoords[1] * DELTATIME)
	r1.output.set_coord(r1.output.coord + vcoords[2] * DELTATIME)
	r2.output.set_coord(r2.output.coord + vcoords[3] * DELTATIME)

	base.location_update()

show(animate=animate)
	
	#print(mass.global_location)
	
#for e in els:
#	print(e.force_model.output_force)

#for i in range(1):
#
##	els[-1].force_model.output_force = gravity_mass
#
##	for i, d in enumerated(reversed(els)):
##		d.force_model.evaluate_input_force()
##		els
#		
##		force_screw = d.force_model.output_force.inverse_transform(d.global_location)
##		print(force_screw)
#
#	for d in els:
#		force_screw = gravity_mass
#		rid = d.rigidity_model.eval_deflection(force_screw)
#		print(rid)
#
#		d.connector.relocate(translate(rid.lin) * rotate(rid.ang.normalize(), numpy.linalg.norm(rid.ang)) * d.con)
#		#print(rid)
#	
#	els[0].location_update()

#disp(els[0])
#zencad.show()