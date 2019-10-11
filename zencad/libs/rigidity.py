# гибкость стержневой конструкции

import zencad
import numpy

from zencad.libs.screw import screw


#class rod_finite_element_model:
#	def __init__(self, E, G, F, Jx, Jy, Jz, l):
#		self.E = E
#		self.G = G
#		self.F = F
#		self.Jx = Jx
#		self.Jy = Jy
#		self.Jz = Jz
#		self.l = l

#		self.flexibility = rod_flexibility_matrix(E, G, F, Jx, Jy, Jz, l)
#		self.rigidity = rod_rigidity_matrix(E, G, F, Jx, Jy, Jz, l)

#	def eval_deflection(self, force_screw):
#		"""расчет винта перемещения выходного звена"""
#		a = self.flexibility.dot(force_screw.to_array())
#		a = a.tolist()[0]
		#print(a)
#		return screw.from_array(a)	

#def gravity_local_force_evaluator(fmodel):
#	pass

class force_model:
	def __init__(self, unit):
		self.parent = unit
		self.output_force = screw()		

	def input_force(self):
		"""Посчитать входную узловую силу балочного элемента на основе 
		информации о выходной и локальной."""

		ltrans = self.parent.location
		lmove = ltrans.translation()
		
		return self.output_force.carry(lmove)

	def visualize(self):
		print("TODO Visualize")

class force_model_mass_point(force_model):
	def __init__(self, unit, mass, vec = (0,0,-9.81)):
		super().__init__(unit)
		self.mass = mass
		self.vec = zencad.to_vector(vec) * self.mass

	#def gravity(self):

	def input_force(self):
		"""Посчитать входную узловую силу балочного элемента на основе 
		информации о выходной и локальной."""

		ltrans = self.parent.location
		gtrans = self.parent.global_location

		lmove = ltrans.translation()
		gravity = zencad.vector3(self.vec)
		gravity = gtrans.inverse()(gravity)

		# гравитация приведенная к входу.
		igravity = zencad.libs.screw.screw_of_vector(vec=gravity, arm=lmove / 2)

		return self.output_force.carry(lmove) + igravity

class force_model_algorithm:
	def __init__(self, base):
		self.base = base

	def _attach(self, unit):
		if not hasattr(unit, "force_model"):
			unit.force_model = force_model(unit)
		for c in unit.childs:
			self._attach(c)

	def attach(self):
		self._attach(self.base)

	def _force_evaluation(self, unit):
		output_force = screw()
		for c in unit.childs:
			loc = unit.global_location.inverse() * c.global_location
			output_force += self._force_evaluation(c).transform(loc) #inverse?

		unit.force_model.output_force = output_force
		#unit.force_model.evaluate_local_force()
		return unit.force_model.input_force()

	def force_evaluation(self):
		self._force_evaluation(self.base)

	def _deformation_evaluation(self, unit):
		fmodel = unit.force_model
		if hasattr(unit, "flexibility_model") and unit.flexibility_model is not None:
			force = fmodel.output_force
			farray = force.to_array()
			fmodel.deformation = zencad.libs.screw.screw.from_array(
				unit.flexibility_model.dot(farray).tolist()[0]
			)
		else:
			fmodel.deformation = None

		#print(fmodel.deformation)
			
		for c in unit.childs:
			self._deformation_evaluation(c)

	def deformation_evaluation(self):
		self._deformation_evaluation(self.base)

	def _apply_deformation(self, unit):
		fmodel = unit.force_model

		if fmodel.deformation is not None:
			mov = zencad.translate(*fmodel.deformation.lin)
			norm = numpy.linalg.norm(fmodel.deformation.ang)
			rot = zencad.rotate(fmodel.deformation.ang / norm, norm)

			unit.location = mov * rot
		#print("location:", unit.location)
		
		for c in unit.childs:
			self._apply_deformation(c)

	def apply_deformation(self):
		self._apply_deformation(self.base)
		self.base.location_update()


#def rigidity_matrix(E, G, F, Jx, Jy, Jz, l):
#	return numpy.matrix(
#		[
#			[E*F/l,  0,             0,             0,       0,            0,           -E*F/l, 0,             0,             0,       0,            0           ],
#			[0,      12*E*Jz/l**3,  0,             0,       0,            6*E*Jz/l**2, 0,      -12*E*Jz/l**3, 0,             0,       0,            6*E*Jz/l**2 ],
#			[0,      0,             12*E*Jy/l**3,  0,       -6*E*Jy/l**2, 0,           0,      0,             -12*E*Jy/l**3, 0,       -6*E*Jy/l**2, 0           ],
#			[0,      0,             0,             G*Jx/l,  0,            0,           0,      0,             0,             -G*Jx/l, 0,            0           ],
#			[0,      0,             -6*E*Jy/l**2,  0,       4*E*Jy/l,     0,           0,      0,             6*E*Jy/l**2,   0,       2*E*Jy/l,     0           ],
#			[0,      6*E*Jz/l**2,   0,             0,       0,            4*E*Jz/l,    0,      -6*E/l**2,     0,             0,       0,            2*E*Jz/l    ],
#			[-E*F/l, 0,             0,             0,       0,            0,           E*F/l,  0,             0,             0,       0,            0           ],
#			[0,      -12*E*Jz/l**3, 0,             0,       0,            -6*E/l**2,   0,      12*E*Jz/l**3,  0,             0,       0,            -6*E*Jz/l**2],
#			[0,      0,             -12*E*Jy/l**3, 0,       6*E*Jy/l**2,  0,           0,      0,             12*E*Jy/l**3,  0,       6*E*Jy/l**2,  0           ],
#			[0,      0,             0,             -G*Jx/l, 0,            0,           0,      0,             0,             G*Jx/l,  0,            0           ],
#			[0,      0,             -6*E*Jy/l**2,  0,       2*E*Jy/l,     0,           0,      0,             6*E*Jy/l**2,   0,       4*E*Jy/l,     0           ],
#			[0,      6*E*Jz/l**2,   0,             0,       0,            2*E*Jz/l,    0,      -6*E*Jz/l**2,  0,             0,       0,            4*E*Jz/l    ]
#		]
#	)


def rod_rigidity_matrix(E, G, F, Jx, Jy, Jz, l):
	return numpy.matrix(
		[
			[E*F/l,  0,             0,             0,       0,            0,          ],
			[0,      12*E*Jz/l**3,  0,             0,       0,            6*E*Jz/l**2,],
			[0,      0,             12*E*Jy/l**3,  0,       -6*E*Jy/l**2, 0,          ],
			[0,      0,             0,             G*Jx/l,  0,            0,          ],
			[0,      0,             -6*E*Jy/l**2,  0,       4*E*Jy/l,     0,          ],
			[0,      6*E*Jz/l**2,   0,             0,       0,            4*E*Jz/l,   ],
		]
	)

def rod_flexibility_matrix(E, G, F, Jx, Jy, Jz, l):
	return numpy.linalg.inv(rod_rigidity_matrix(E, G, F, Jx, Jy, Jz, l))
