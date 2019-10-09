"""Бивектор углового и линейного параметра"""

import zencad
import numpy

class screw:
	"""Геометрический винт. 

	Состоит из угловой и линейной части."""

	def __init__(self, ang=(0,0,0), lin=(0,0,0)):
		self.ang = zencad.to_vector(ang)
		self.lin = zencad.to_vector(lin)

	def carry(self, trans):
		"""Перенос бивектора в другую точку приложения.

		Detail
		------
		Формула TODO
		"""
		
		print("TODO carry")
		return screw(self.ang, self.lin)

	def to_array(self):
		"""Массив имеет обратный принятому в screw порядку"""
		return numpy.array([*self.lin, *self.ang])

	@staticmethod
	def from_trans(trans):
		"""Создать винт на основе объекта трансформации zencad.transform
		
		Detail:
		-------
		Масштабирование игнорируется.
		"""

		print("TODO fromtrans")
		return screw()


	@staticmethod
	def from_array(a):
		return screw(ang=(a[3], a[4], a[5]), lin=(a[0], a[1], a[2]))

	def __str__(self):
		return "(a:{},l:{})".format(self.ang, self.lin)

	def inverse_transform(self, trans):
		trans = trans.inverse()
		return screw(ang=trans(self.ang), lin=trans(self.lin))