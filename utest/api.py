#!/usr/bin/env python3
# coding:utf-8

import sys

sys.path.insert(0, "..")

import unittest
import zencad

import prim1d_test
import prim2d_test
import prim3d_test
import ops3d_test
import ops1d2d_test
import boolean_test
import math_test
import trans_test
import rigidity_test
import curve3_test
import curve2_test


def execute_test(test):
    print()
    print("TEST:")
    unittest.TextTestRunner(verbosity=2).run(
        unittest.TestLoader().loadTestsFromModule(test)
    )


if __name__ == "__main__":
    execute_test(prim1d_test)
    execute_test(prim2d_test)
    execute_test(prim3d_test)
    execute_test(ops3d_test)
    execute_test(ops1d2d_test)
    execute_test(boolean_test)
    execute_test(math_test)
    execute_test(trans_test)
    execute_test(rigidity_test)
    execute_test(curve3_test)
    execute_test(curve2_test)
