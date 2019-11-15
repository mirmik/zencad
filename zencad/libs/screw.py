"""Бивектор углового и линейного параметра"""

import zencad
import numpy

class screw:
	"""Геометрический винт. 

	Состоит из угловой и линейной части."""

	def __init__(self, ang=(0,0,0), lin=(0,0,0)):
		self.ang = zencad.to_vector(ang)
		self.lin = zencad.to_vector(lin)

	def __add__(self, oth):
		return screw(self.ang + oth.ang, self.lin + oth.lin)

	def __sub__(self, oth):
		return screw(self.ang - oth.ang, self.lin - oth.lin)

	def __mul__(self, oth):
		return screw(self.ang * oth, self.lin * oth)

	def elementwise_mul(self, oth):
		#return screw((self.ang * oth.ang), self.lin * oth.lin)
		r = self.to_array() * oth.to_array()
		return screw.from_array(r)

	def __neg__(self):
		return screw(-self.ang, -self.lin)

	def scale(self, oth):
		return screw(self.ang * oth, self.lin * oth)

	def __iadd__(self, oth):
		self.ang += oth.ang
		self.lin += oth.lin
		return self

	def carry(self, arm):
		"""Перенос бивектора в другую точку приложения.

		Detail
		------
		Формула TODO
		"""
		return screw(
			self.ang + arm.cross(self.lin), 
			self.lin)

	
	def to_array(self):
		"""Массив имеет обратный принятому в screw порядку"""
		return numpy.array([*self.lin, *self.ang])

	@staticmethod
	def from_trans(trans):
		lin = trans.translation()
		ang = trans.rotation().rotation_vector()
		return screw(lin=lin, ang=ang)

	def to_trans(self):
		trans0 = zencad.translate(*self.lin)
		
		rot_mul = self.ang.length()
		if rot_mul == 0:
			return trans0
		else:
			rot_dim = self.ang.normalize()
			trans1 = zencad.rotate(rot_dim, rot_mul)
			return trans0 * trans1 
		
	@staticmethod
	def from_array(a):
		return screw(ang=(a[3], a[4], a[5]), lin=(a[0], a[1], a[2]))

	def __str__(self):
		return "(a:{},l:{})".format(self.ang, self.lin)

	def __repr__(self):
		return "screw({},{})".format(self.ang,self.lin)

	def inverse_rotate_by(self, trans):
		q = trans.rotation().inverse()
		return screw(ang=q.rotate(self.ang), lin=q.rotate(self.lin))

	def rotate_by(self, trans):
		return screw(ang=trans(self.ang), lin=trans(self.lin))

def screw_of_vector(vec, arm):
	return screw(lin=vec, ang=arm.cross(vec))