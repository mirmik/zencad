import unittest
import zencad
import zencad.geom.curve3
import numpy
import math

class Curve3(unittest.TestCase):
	def setUp(self):
		zencad.lazy.encache = False
		zencad.lazy.decache = False
		zencad.lazy.fastdo = True

	def test_api(self):
		a = zencad.geom.curve3.interpolate([(0,0,0), (0,0,1)],[(0,0,1), (0,0,1)], closed=False)
		b = zencad.geom.curve3.interpolate([(0,0,0), (0,0,1)], closed=False)

		self.assertEqual( a.value(0), zencad.point3(0,0,0) )
		self.assertEqual( a.value(1), zencad.point3(0,0,1) )
		self.assertEqual( a.value(0.5), zencad.point3(0,0,0.5) )


		