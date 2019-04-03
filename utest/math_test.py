import unittest
from zencad import *


def early(a, b):
    if abs(a.x - b.x) > 0.0001:
        return False
    if abs(a.y - b.y) > 0.0001:
        return False
    if abs(a.z - b.z) > 0.0001:
        return False
    return True


class MathTest(unittest.TestCase):
    def test_math(self):
        self.assertTrue(
            early(
                zencad.point3(1, 2, 3) + zencad.vector3(7, 6, 5), zencad.point3(8, 8, 8)
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
                zencad.point(1, 2, 3) - zencad.point3(7, 6, 5),
                zencad.vector3(-6, -4, -2),
            )
        )
        self.assertTrue(early(zencad.vector(3, 6, 9) * 3, zencad.vector3(9, 18, 27)))
        self.assertTrue(early(zencad.vector(3, 6, 9) / 3, zencad.vector3(1, 2, 3)))

        with self.assertRaises(TypeError):
            zencad.point(1, 2, 3) * 3

        with self.assertRaises(TypeError):
            zencad.point(1, 2, 3) / 3
