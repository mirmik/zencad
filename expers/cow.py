#!/usr/bin/env zencad

import numpy

from zencad import *
import zencad.assemble
from zencad.libs.screw import screw
from zencad.libs.inertia import inertia

#m = box(3)

class cow(zencad.assemble.unit):
	r = 10

	class force_producer(zencad.assemble.unit):
		def __init__(self, parent, location):
			super().__init__(parent=parent, location=location)
			self.set_shape(cylinder(r=1,h=3))
			self.marshal = vector3(0,0,1)
			self.signal = 0

		def set_control_signal(self, signal):
			self.signal = signal

		def get_force_screw(self):
			return screw(lin=self.marshal * self.signal, ang=(0,0,0))

		def serve(self, delta):
			pass


	class torque_producer(zencad.assemble.unit):
		def __init__(self, parent, location):
			super().__init__(parent=parent, location=location)
			self.set_shape(cylinder(r=1,h=3))
			self.marshal = vector3(0,0,1)
			self.signal = 0

		def set_control_signal(self, signal):
			self.signal = signal

		def get_force_screw(self):
			return screw(ang=self.marshal * self.signal, lin=(0,0,0))

		def serve(self, delta):
			pass

	def __init__(self):
		super().__init__()
		self.inertia = inertia(1, numpy.diag([1,1,1]))
		self.impulse_screw = screw()
		self.set_shape(zencad.sphere(self.r))
		self.make_drivers()

	def add_force_producer(self, trans):
		self.force_producer_list.append(self.force_producer(parent=self, location=trans))

	def add_torque_producer(self, trans):
		self.force_producer_list.append(self.torque_producer(parent=self, location=trans))

	def make_drivers(self):
		self.force_producer_list = []
		self.add_force_producer(rotateY(-deg(90)))
		self.add_force_producer(rotateX(deg(90)))
		self.add_force_producer(nulltrans())
		self.add_torque_producer(rotateY(-deg(90)))
		self.add_torque_producer(rotateX(deg(90)))
		self.add_torque_producer(nulltrans())

	def serve(self, delta):
		for f in self.force_producer_list:
			f.serve(delta)

		fscrews = [ f.get_force_screw()
			.inverse_transform(f.location) for f in self.force_producer_list ]

		fscrew = screw()
		for f in fscrews:
			fscrew += f

		self.impulse_screw += fscrew.scale(delta) 

		self.speed_screw = self.inertia.impulse_to_speed(self.impulse_screw)
		speed_screw_delta = self.speed_screw.scale(delta)

		speed_screw_delta_trans = speed_screw_delta.to_trans()
		self.location = self.location * speed_screw_delta_trans

		self.speed_screw = self.speed_screw.inverse_transform(speed_screw_delta_trans)

		print(self.speed_screw)

		self.location_update()

cow = cow()

cow.force_producer_list[0].set_control_signal(0.1)
cow.force_producer_list[1].set_control_signal(0)
cow.force_producer_list[2].set_control_signal(0)
cow.force_producer_list[3].set_control_signal(0)
cow.force_producer_list[4].set_control_signal(0)
cow.force_producer_list[5].set_control_signal(0.001)


def animate(wdg):
	cow.serve(0.1)


display(cow)
show(animate = animate)
