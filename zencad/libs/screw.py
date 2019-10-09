"""Бивектор углового и линейного параметра"""

import zencad

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

	@classmethod
	def fromtrans(trans):
		"""Создать винт на основе объекта трансформации zencad.transform
		
		Detail:
		-------
		Масштабирование игнорируется.
		"""

		print("TODO fromtrans")
		return screw()