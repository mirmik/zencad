import unittest
import zencad
import zencad.libs.rigidity
import numpy
import math

class Rigidity(unittest.TestCase):
	def setUp(self):
		zencad.lazy.encache = False
		zencad.lazy.decache = False
		zencad.lazy.fastdo = True

	def test_rigidity_matrix_symmetric(self):
		E = 1
		G = 2
		F = 3
		Jx = 4
		Jy = 5
		Jz = 6
		l =7

		mat = zencad.libs.rigidity.rigidity_matrix(E, G, F, Jx, Jy, Jz, l)
		discriminant = numpy.linalg.det(mat)

		for i in range(12):
			for j in range(12):
				self.assertEqual(mat[i,j], mat[j,i])

		self.assertEqual(discriminant, 0)