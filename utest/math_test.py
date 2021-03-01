import unittest
from zencad import *

from OCC.Core.gp import gp_Dir, gp_Vec, gp_Pnt

def early(a, b):
    if abs(a.x - b.x) > 0.0001:
        return False
    if abs(a.y - b.y) > 0.0001:
        return False
    if abs(a.z - b.z) > 0.0001:
        return False
    return True


class MathTest(unittest.TestCase):
    def test_constructor(self):
        self.assertEqual(point3(0,0,1), point3(gp_Dir(0,0,1)))
        self.assertEqual(point3(0,1,1), point3(gp_Vec(0,1,1)))
        self.assertEqual(point3(1,0,1), point3(gp_Pnt(1,0,1)))

        self.assertEqual(vector3(0,0,1), vector3(gp_Dir(0,0,1)))
        self.assertEqual(vector3(0,1,1), vector3(gp_Vec(0,1,1)))
        self.assertEqual(vector3(1,0,1), vector3(gp_Pnt(1,0,1)))

    def test_math(self):
        self.assertTrue(
            early(
                zencad.point3(1, 2, 3) + zencad.vector3(7,
                                                        6, 5), zencad.point3(8, 8, 8)
            )
        )
        self.assertTrue(
            early(
                zencad.point3(1, 2, 3) - zencad.vector3(7, 6, 5),
                zencad.point3(-6, -4, -2),
            )
        )
        self.assertTrue(
            early(
                zencad.vector3(1, 2, 3) + zencad.vector3(7, 6, 5),
                zencad.vector3(8, 8, 8),
            )
        )
        self.assertTrue(
            early(
                zencad.vector3(1, 2, 3) - zencad.vector3(7, 6, 5),
                zencad.vector3(-6, -4, -2),
            )
        )
        self.assertTrue(
            early(
                zencad.point3(1, 2, 3) - zencad.point3(7, 6, 5),
                zencad.vector3(-6, -4, -2),
            )
        )
        self.assertTrue(early(zencad.vector3(3, 6, 9) *
                              3, zencad.vector3(9, 18, 27)))
        self.assertTrue(early(zencad.vector3(3, 6, 9) /
                              3, zencad.vector3(1, 2, 3)))
