#!/usr/bin/env python3

import numpy
import time

import zencad.malgo
from zencad import *
import zencad.assemble
from zencad.libs.screw import screw
from zencad.libs.inertia import inertia

#m = box(3)
model = (box(20,10,10,center=True)+
			box(20,10,10,center=True).rotateZ(deg(90))+
			box(20,10,10,center=True).rotateY(deg(90))
)

class cow(zencad.assemble.unit):
	r = 10

	class force_producer(zencad.assemble.unit):
		def __init__(self, parent, location):
			super().__init__(parent=parent, location=location)
			self.add_shape(cylinder(r=1,h=3,center=True))
			self.marshal = vector3(0,0,1)
			self.signal = 0

		def set_control_signal(self, signal):
			self.signal = signal

		def get_force_screw(self):
			return screw(lin=self.marshal * self.signal, ang=(0,0,0))

		def sensivity(self):
			return screw(lin=self.marshal, ang=(0,0,0))

		def serve(self, delta):
			pass


	class torque_producer(zencad.assemble.unit):
		def __init__(self, parent, location):
			super().__init__(parent=parent, location=location)
			self.add_shape(cylinder(r=1,h=3))
			self.marshal = vector3(0,0,1)
			self.signal = 0

		def set_control_signal(self, signal):
			self.signal = signal

		def get_force_screw(self):
			return screw(ang=self.marshal * self.signal, lin=(0,0,0))

		def sensivity(self):
			return screw(ang=self.marshal, lin=(0,0,0))

		def serve(self, delta):
			pass

	def __init__(self):
		super().__init__()
		self.inertia = inertia(1, numpy.diag([1,1,1]))
		self.impulse_screw = screw()
		self.add_shape(
			#zencad.sphere(self.r)
			model
		)
		self.make_drivers()

	def add_force_producer(self, trans):
		self.force_producer_list.append(self.force_producer(parent=self, location=trans))

	def add_torque_producer(self, trans):
		self.force_producer_list.append(self.torque_producer(parent=self, location=trans))

	def make_drivers(self):
		self.force_producer_list = []
		self.add_force_producer(right(10))
		self.add_force_producer(left(10))
		self.add_force_producer(forw(10))
		self.add_force_producer(back(10))
		self.add_force_producer(left(10) * rotateX(deg(90)))
		self.add_force_producer(right(10) * rotateX(deg(90)))
		self.add_force_producer(forw(10) * rotateY(deg(90)))
		self.add_force_producer(back(10) * rotateY(deg(90)))
		
		#self.add_force_producer(up(10) * rotateY(deg(90)))
		#self.add_force_producer(down(10) * rotateY(deg(90)))
		#self.add_force_producer(up(10) * rotateX(deg(90)))
		#self.add_force_producer(down(10) * rotateX(deg(90)))
		#self.add_torque_producer(rotateY(-deg(90)))
		#self.add_torque_producer(rotateX(deg(90)))
		#self.add_torque_producer(nulltrans())

	def serve(self, delta):
		for f in self.force_producer_list:
			f.serve(delta)

		fscrews = [ f.get_force_screw()
			.rotate_by(f.location).carry(-f.location.translation()) for f in self.force_producer_list ]

		fscrew = screw()
		for f in fscrews:
			fscrew += f

		self.impulse_screw += fscrew.scale(delta) 

		self.speed_screw = self.inertia.impulse_to_speed(self.impulse_screw)
		speed_screw_delta = self.speed_screw.scale(delta)

		speed_screw_delta_trans = speed_screw_delta.to_trans()
		self.location = self.location * speed_screw_delta_trans

		self.impulse_screw = self.impulse_screw.inverse_rotate_by(speed_screw_delta_trans)
		self.speed_screw = self.speed_screw.inverse_rotate_by(speed_screw_delta_trans)

		self.location_update(deep=True)

	def sensivities(self):
		sens = [ f.sensivity().rotate_by(f.location).carry(-f.location.translation()) 
			for f in self.force_producer_list ]

		return sens

	def solve_control_equations(self, target, sens):
		return zencad.malgo.svd_backpack(target, sens)

	def set_control(self, control_screw):
		#control_screw = control_screw.inverse_rotate_by(self.location)
		control_screw = control_screw.to_array()
		sens = [ s.to_array() for s in self.sensivities() ]
		koeffs = self.solve_control_equations(control_screw, sens)[0]
		#print(koeffs)

		for i in range(len(self.force_producer_list)):
			self.force_producer_list[i].set_control_signal(koeffs[i])

cow = cow()

hl(model.transform(translate(100,100,100) * rotate(v=(1,1,1), a=deg(180))))
hl(model.transform(translate(-100,100,100) * rotate(v=(1,1,1), a=deg(-90))))
hl(model)

start_time = time.time()
last_time = start_time
def animate(wdg):
	global last_time
	curtime = time.time()
	delta = curtime - last_time
	last_time=curtime
	from_start = curtime - start_time


	cow.serve(delta)
	speed_screw = cow.speed_screw

	if from_start < 7:
		target_location = translate(100,100,100) * rotate(v=(1,1,1), a=deg(180))
	elif from_start < 14:
		target_location = translate(-100,100,100) * rotate(v=(1,1,1), a=deg(-90))
	else: 
		target_location = nulltrans()

	location_error = cow.global_location.inverse() * target_location

	location_error_screw = screw.from_trans(location_error)	 
	speed_error_screw = -speed_screw

	T = 1
	ksi = 0.85
	
	def koeffs(T, ksi, A):
		K1 = A/T**2
		K0 = 2*ksi*K1*T
		return K0, K1

	K0_m, K1_m = koeffs(T, ksi, cow.inertia.mass)
	K0_I0, K1_I0 = koeffs(T, ksi, cow.inertia.matrix[0,0])
	K0_I1, K1_I1 = koeffs(T, ksi, cow.inertia.matrix[1,1])
	K0_I2, K1_I2 = koeffs(T, ksi, cow.inertia.matrix[2,2])
	
	K0 = screw(lin=(K0_m, K0_m, K0_m), ang=(K0_I0, K0_I1, K0_I2))
	K1 = screw(lin=(K1_m, K1_m, K1_m), ang=(K1_I0, K1_I1, K1_I2))

	#K0 = 2.2
	#K1 = 1.4
	control_signal = (speed_error_screw.elementwise_mul(K0) 
		+ location_error_screw.elementwise_mul(K1))
	#control_signal = control_signal.elementwise_mul(screw(lin=(1,1,1),ang=(1,1,1)))

	#print(location_error_screw)
	#control_signal = screw(lin=(0,1,0), ang=(0,0,0))
	cow.set_control(control_signal)

	#cow.force_producer_list[0].set_control_signal(-0.1 * speed_screw.lin[0] + 0.1 * (10 - cow.location.translation()[0]))
	#cow.force_producer_list[1].set_control_signal(0)
	#cow.force_producer_list[2].set_control_signal(0)
	#cow.force_producer_list[3].set_control_signal(0)
	#cow.force_producer_list[4].set_control_signal(0)
	#cow.force_producer_list[5].set_control_signal(0)

display(cow)
show(animate = animate)
