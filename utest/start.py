#!/usr/bin/python3
#coding:utf-8

import sys
sys.path.insert(0, "..")

import unittest
import zencad

import prim3d_test

class ZenCadApiProbber(unittest.TestCase):
	def test_api_probber(self):
		zencad.box(1,2,3).unlazy()
		zencad.cylinder(r=3,h=3).unlazy()
		zencad.cylinder(r=3,h=3,angle=20).unlazy()
		zencad.cone(r1=3,r2=6,h=3).unlazy()
		#zencad.cone(r1=3,r2=6,h=3,angle=20).unlazy()
		zencad.torus(r1=3,r2=1).unlazy()
		#zencad.torus(r1=3,r2=1,angle=20).unlazy()
		zencad.sphere(r=3).unlazy()
	
if __name__ == '__main__':
	prim3d = unittest.TestLoader().loadTestsFromModule(prim3d_test)
	unittest.TextTestRunner(verbosity=2).run(prim3d)
	
	unittest.main()
