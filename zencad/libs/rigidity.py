"""Модуль для визуализации и учёта упругости в кинематических цепях."""

import zencad
import numpy

from zencad.libs.screw import screw

class rod_finite_element_model:
	def __init__(self, E, G, F, Jx, Jy, Jz, l):
		self.E = E
		self.G = G
		self.F = F
		self.Jx = Jx
		self.Jy = Jy
		self.Jz = Jz
		self.l = l

		self.flexibility = rod_flexibility_matrix(E, G, F, Jx, Jy, Jz, l)
		self.rigidity = rod_rigidity_matrix(E, G, F, Jx, Jy, Jz, l)

	def eval_deflection(self, force_screw):
		"""расчет винта перемещения выходного звена"""
		a = self.flexibility.dot(force_screw.to_array())
		a = a.tolist()[0]
		#print(a)
		return screw.from_array(a)	

class force_model:
	def __init__(self, inunit, outunit):
		self.inunit = inunit
		self.outunit = outunit
		self.output_force = None
		self.input_force = None
		self.local_force_evaluator = None

	def evaluate_input_force(self):
		self.input_force = self.output_force

		#if self.inunit.parent and self.inunit.parent.force_model:
		#	self.inunit.parent.force_model.output_force = self.input_force

	def visualize(self):
		print("TODO Visualize")


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
