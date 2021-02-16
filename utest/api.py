#!/usr/bin/env python3
# coding:utf-8

import sys
import traceback
print("api.py")


sys.path.insert(0, "..")

print("import")
try:
    print("import pyservoce")
    import pyservoce

    print("import traceback")
    import traceback

    print("import unittest")
    import unittest

    print("import PyQt5")
    import PyQt5

    print("import zencad")
    import zencad

    print("import tests")
    import prim1d_test
    import prim2d_test
    import prim3d_test
    import ops3d_test
    import ops1d2d_test
    import boolean_test
    import math_test
    import trans_test
    import curve3_test
    import curve2_test
    import reflection
except Exception as ex:
    print(ex)
    traceback.print_exc()


print("import ... finish")


def execute_test(test):
    print()
    print("TEST:")
    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.TestLoader().loadTestsFromModule(test)
    )

    if len(result.errors) != 0:
        sys.exit(-1)


if __name__ == "__main__":
    print("main")
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
    execute_test(reflection)
