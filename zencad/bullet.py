from zencad.libs.bullet import * 
import pybullet

class force_controller:
	def __init__(self, simulation, kunit):
		self.simulation = simulation
		self.kunit = kunit
		self.force = 0
	
	def index(self):
		return self.kunit.simulation_hint2

	def bodyID(self):
		return self.kunit.pybullet_base.boxId

	def set_force(self, force):
		self.force = force

	def serve(self, delta):
		pybullet.setJointMotorControl2(bodyUniqueId=self.bodyID(), 
			jointIndex=self.index(),
			controlMode=pybullet.TORQUE_CONTROL,
			force=self.force)

		self.kunit.update_coord(self.coord()) 

	def speed(self):
		info = pybullet.getJointState(self.bodyID(), self.index())
		return info[1]

	def coord(self):
		info = pybullet.getJointState(self.bodyID(), self.index())
		return info[0]

class speed_controller(force_controller):
	def __init__(self, simulation, kunit, kp=0, kd=0, ki=0):
		super().__init__(kunit=kunit, simulation=simulation)
		self.kp = kp
		self.kd = kd
		self.ki = ki
		self.kif = 0
		self.target = 0
		self.last_speed = 0
		self.error_integral = 0

	def set_target(self, target):
		self.target = target

	def serve(self, delta):
		spdsig = self.speed()
		spddelta = (self.last_speed - spdsig)
		
		error = self.target - spdsig
		self.error_integral += error * delta - self.error_integral * self.kif * delta

		self.setted_force = error * self.kp + self.error_integral * self.ki + spddelta * self.kd

		self.set_force(self.setted_force)

		self.last_speed = spdsig
		super().serve(delta)

	def set_params(self, K, T, ksi):
		self.ki = 1 / (T**2)
		self.kp = 2 * ksi * T * self.ki

		self.ki = self.ki * K
		self.kp = self.kp * K

	def set_koeffs(self, kp=0, kd=0, ki=0, kif=0):
		self.kp = kp
		self.kd = kd
		self.ki = ki
		self.kif = kif
		


class servo_controller(force_controller):
	def __init__(self, simulation, kunit):
		super().__init__(kunit=kunit, simulation=simulation)
		self.kpos = 0
		self.kspd = 0
		self.kspd_i = 0
		self.kspd_if = 0
		self.speed_error_integral = 0 
		self.speed_target = 0
		self.position_target = 0
		self.maxforce = None

		self.filtered_spdsig = 0
		self.filtered_possig = 0

	def set_gear_ratio(self, gear):
		pass
		#pybullet.changeConstraint(self.bodyID(), self.index(), gearRatio=gear)
		
	def set_speed_target(self, target):
		self.speed_target = target

	def set_position_target(self, target):
		self.position_target = target

	def serve(self, delta):
		spdsig = self.speed()
		possig = self.coord()

		self.filtered_spdsig += (spdsig - self.filtered_spdsig) * 0.01
		self.filtered_possig += (possig - self.filtered_possig) * 0.01

		self.position_target = self.position_target + self.speed_target * delta

		poserr = self.position_target - self.filtered_possig
		spderr = self.speed_target - self.filtered_spdsig

		self.speed_error_integral += (spderr - self.speed_error_integral * self.kspd_if) * delta 

		self.setted_force = poserr * self.kpos + spderr * self.kspd + self.speed_error_integral * self.kspd_i
		if abs(self.setted_force) > self.maxforce:
			self.setted_force = self.setted_force / abs(self.setted_force) * self.maxforce

		self.set_force(self.setted_force)
		super().serve(delta)


	def set_koeffs(self, kpos=0, kspd=0, kspd_i=0, kspd_if=0, maxforce=None):
		self.kpos = kpos
		self.kspd = kspd
		self.kspd_i = kspd_i
		self.kspd_if = kspd_if
		self.maxforce = maxforce
		
class pid:
	def __init__(self, kp, ki, kd=0, dkoeff=0):
		self.kp = kp 
		self.ki = ki
		self.kd = kd
		self.dkoeff = dkoeff
		self.aper = 0
		self.integral = 0
		self.last = 0

	def serve(self, input, delta):
		self.integral += input * delta
		#diff = input - self.aper
		#self.aper += diff * self.dkoeff
		diff = input - self.last
		self._value = input * self.kp + self.integral * self.ki + diff * self.kd
		self.last = input

	def value(self):
		return self._value

	@staticmethod
	def by_params(T, ksi, M=1):
		T=T/M
		ksi=ksi*M
		Ki = 1/(T*T)
		Kp = 2*ksi*T*Ki
		return pid(kp=Kp, ki=Ki, kd=0, dkoeff=0)

class servo_controller2(force_controller):
	def __init__(self, simulation, kunit):
		super().__init__(kunit=kunit, simulation=simulation)
		self.speed_target = 0
		self.position_target = 0
		self.filtered_force = 0
		self.spd2 = 0
		self.filtered_spd2 = 0

	def init(self):
		self.position_target = self.coord()
		self.speed_target = self.speed()

	def set_speed_target(self, target):
		self.speed_target = target

	def set_position_target(self, target):
		self.position_target = target

	def set_speed2(self, spd2):
		self.spd2 = spd2

	def serve(self, delta):
		self.filtered_spd2 += (self.spd2 - self.filtered_spd2) * delta
		self.position_target += self.filtered_spd2 * delta

		spdsig = self.speed()
		possig = self.coord()

		self.filtered_spdsig += (spdsig - self.filtered_spdsig) * 0.01
		self.filtered_possig += (possig - self.filtered_possig) * 0.01

		poserr = self.position_target - self.filtered_possig
		spderr = self.speed_target - self.filtered_spdsig

		self.set_speed_target( poserr * self.kp )
		evaluated_force = spderr * self.kv

		self.filtered_force += (evaluated_force - self.filtered_force) * self.filter
		
		self.set_force(self.filtered_force)
		super().serve(delta)

	def set_koeffs(self, kv=0, kp=0, filt=1):
		self.kv = kv	
		self.kp = kp
		self.filter = filt

class servo_controller3(force_controller):
	def __init__(self, simulation, kunit):
		super().__init__(kunit=kunit, simulation=simulation)
		self.speed_target = 0
		self.position_target = 0
		self.filtered_force = 0
		self.filtered_force2 = 0
		self.spd2 = 0
		self.filtered_spdsig = 0
		self.filtered_possig = 0
		self.filtered_spd2 = 0

	def init(self):
		self.position_target = self.coord()
		self.speed_target = self.speed()

	def set_speed_target(self, target):
		self.speed_target = target

	def set_position_target(self, target):
		self.position_target = target

	def set_speed2(self, spd2):
		self.spd2 = spd2

	def serve(self, delta):
		self.filtered_spd2 += (self.spd2 - self.filtered_spd2) * 1
		self.position_target += self.filtered_spd2 * delta

		spdsig = self.speed()
		possig = self.coord()

		self.filtered_spdsig += (spdsig - self.filtered_spdsig) * 1
		self.filtered_possig += (possig - self.filtered_possig) * 1

		poserr = self.position_target - self.filtered_possig
		self.pidpos.serve(poserr, delta)
		self.set_speed_target( self.pidpos.value() )

		spderr = self.speed_target - self.filtered_spdsig
		self.pidspd.serve(spderr, delta)
		evaluated_force = self.pidspd.value()

		self.filtered_force += (evaluated_force - self.filtered_force) * self.filter

		final_force = self.filtered_force

		if self.maxforce:
			if abs(final_force) > self.maxforce: final_force = final_force / abs(final_force) * self.maxforce		

		self.set_force(final_force)

		super().serve(delta)

	def serve_spd_only(self, delta):
		spdsig = self.speed()
		spderr = self.speed_target - spdsig

		self.pidspd.serve(spderr, delta)
		evaluated_force = self.pidspd.value()

		final_force = self.filtered_force
		if self.maxforce:
			if abs(final_force) > self.maxforce: final_force = final_force / abs(final_force) * self.maxforce		
		self.set_force(final_force)
		super().serve(delta)

	def set_regs(self, pidspd, pidpos, filt=1, maxforce=None):
		self.pidspd = pidspd	
		self.pidpos = pidpos
		self.filter = filt
		self.maxforce = maxforce
