import unittest
import zencad
import math


def early(a, b):
    if abs(a.x - b.x) > 0.0001:
        return False
    if abs(a.y - b.y) > 0.0001:
        return False
    if abs(a.z - b.z) > 0.0001:
        return False
    return True


def vertex_set_issame(a, b):
    for x in a:
        for y in b:
            if early(x, y):
                break
        else:
            return False

    for x in b:
        for y in a:
            if early(x, y):
                break
        else:
            return False

    return True


class GeneralTransformation(unittest.TestCase):
    def setUp(self):
        zencad.lazy.encache = False
        zencad.lazy.decache = False
        zencad.lazy.fastdo = True

    def test_scale(self):
        b = zencad.box(10, 10, 10)
        t = zencad.box(20, 30, 40)
        scale = zencad.scaleXYZ(2, 3, 4)

        r = scale(b)
        r = b.transform(scale)

        self.assertTrue(vertex_set_issame(r.vertices(), t.vertices()))

    def test_scaleX(self):
        b = zencad.box(10, 10, 10)
        t = zencad.box(20, 10, 10)
        scale = zencad.scaleX(2)

        r = scale(b)
        r = b.transform(scale)

        self.assertTrue(vertex_set_issame(r.vertices(), t.vertices()))

    def test_scaleY(self):
        b = zencad.box(10, 10, 10)
        t = zencad.box(10, 30, 10)
        scale = zencad.scaleY(3)

        r = scale(b)
        r = b.transform(scale)

        self.assertTrue(vertex_set_issame(r.vertices(), t.vertices()))

    def test_scaleZ(self):
        b = zencad.box(10, 10, 10)
        t = zencad.box(10, 10, 40)
        scale = zencad.scaleZ(4)

        r = scale(b)
        r = b.transform(scale)

        self.assertTrue(vertex_set_issame(r.vertices(), t.vertices()))
