import zencad.libs.screw
import zencad
from zencad.libs.screw import screw
import numpy

class inertia:
	def __init__(self, mass, matrix):
		self.matrix = numpy.matrix(matrix)
		self.invmatrix = numpy.linalg.inv(self.matrix)
		self.mass = mass

	def produce_impulse_screw(self, force_screw):
		lin = force_screw.lin / self.mass
		ang = self.invmatrix * numpy.asarray(force_screw.ang).reshape((3,1))
		return screw(ang=zencad.vector3(ang[0,0], ang[1,0], ang[2,0]), lin=lin)
