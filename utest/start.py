#!/usr/bin/env python3
#coding:utf-8

import sys
sys.path.insert(0, "..")

import unittest
import zencad

import prim1d_test
import prim2d_test
import prim3d_test
	
def execute_test(test):
	print()
	print("TEST:")
	unittest.TextTestRunner(verbosity=2).run(unittest.TestLoader().loadTestsFromModule(test))

if __name__ == '__main__':
	execute_test(prim1d_test)
	execute_test(prim2d_test)
	execute_test(prim3d_test)
