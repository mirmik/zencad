import unittest
import zencad

class Ops1d2dProbe(unittest.TestCase):
	def setUp(self):
		zencad.lazy.encache=False
		zencad.lazy.decache=False
		zencad.lazy.fastdo=True