"""Бивектор углового и линейного параметра"""

import zencad

class screw:
	def __init__(self, ang, lin):
		self.ang = zencad.to_vector(ang)
		self.lin = zencad.to_vector(lin)

	