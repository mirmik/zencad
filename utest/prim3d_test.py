import unittest
from zencad import *

class Prim3dProbber(unittest.TestCase):
	def test_box(self):
		m = box(10,20,30)

		test = set([
			point3(0.000000,0.000000,0.000000), 
			point3(0.000000,0.000000,30.000000), 
			point3(0.000000,20.000000,0.000000), 
			point3(0.000000,20.000000,30.000000), 
			point3(10.000000,0.000000,0.000000), 
			point3(10.000000,0.000000,30.000000), 
			point3(10.000000,20.000000,0.000000), 
			point3(10.000000,20.000000,30.000000)
		])

		vertices = m.vertices().unlazy()

		self.assertEqual(set(test), set(vertices))		

	def test_cylinder(self):
		m = cylinder(r = 10, h = 20)

		test = [
			point3(10.000000,-0.000000, 0.000000), 
			point3(10.000000,-0.000000, 20.000000)
		]

		self.assertEqual(m.vertices().unlazy(), test)
