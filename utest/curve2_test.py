import unittest
import zencad
import numpy
import math

class Curve2(unittest.TestCase):
	def setUp(self):
		zencad.lazy.encache = False
		zencad.lazy.decache = False
		zencad.lazy.fastdo = True

	def test_api(self):
		print("TODO Curve2")
		