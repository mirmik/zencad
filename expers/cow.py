#!/usr/bin/env zencad

from zencad import *
import zencad.assemble
from zencad.libs.screw import screw

#m = box(3)

class cow(zencad.assemble.unit):
	r = 10

	class force_producer(zencad.assemble.unit):
		def __init__(self, parent, location):
			super().__init__(parent=parent, location=location)
			self.set_shape(cylinder(r=1,h=3))
			self.marshal = vector3(0,0,1)

		def set_control_signal(self, signal):
			self.signal = signal

		def get_force(self):
			return self.marshal * self.signal

		def serve(self, delta):
			pass

	def __init__(self):
		super().__init__()
		self.set_shape(zencad.sphere(self.r))
		self.make_drivers()

	def add_force_producer(self, trans):
		self.force_producer_list.append(self.force_producer(parent=self, location=trans))

	def make_drivers(self):
		self.force_producer_list = []
		self.add_force_producer(nulltrans())
		self.add_force_producer(rotateX(deg(90)))
		self.add_force_producer(rotateY(deg(90)))

	def serve(self, delta):
		for f in force_producer_list:
			f.serve(delta)

		fscrews = [ screw(ang=(0,0,0), lin=f.get_force())
			.inverse_transform(f.location) for f in force_producer_list ]

		fscrew = sum(fscrews)
		print(fscrew)

cow = cow()



display(cow)
show()
