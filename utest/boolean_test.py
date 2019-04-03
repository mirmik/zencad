import unittest
import zencad


class BooleanProbe(unittest.TestCase):
    def setUp(self):
        zencad.lazy.encache = False
        zencad.lazy.decache = False
        zencad.lazy.fastdo = True

    def test_union_probe(self):
        a = zencad.box(10)
        b = zencad.sphere(10)
        c = zencad.cone(5, 2, h=20)

        f1 = zencad.union([a, b, c])
        f2 = a + b + c
        f3 = zencad.union([c, a, b])
        f4 = c + a + b

        self.assertEqual(f1.vertices().unlazy(), f2.vertices().unlazy())
        self.assertEqual(f1.vertices().unlazy(), f3.vertices().unlazy())
        self.assertEqual(f1.vertices().unlazy(), f4.vertices().unlazy())

    def test_intersect_probe(self):
        a = zencad.box(10)
        b = zencad.sphere(10)
        c = zencad.cone(5, 2, h=20)

        f1 = zencad.intersect([a, b, c])
        f2 = a ^ b ^ c
        f3 = zencad.intersect([c, a, b])
        f4 = c ^ a ^ b

        self.assertEqual(f1.vertices().unlazy(), f2.vertices().unlazy())
        self.assertEqual(f1.vertices().unlazy(), f3.vertices().unlazy())
        self.assertEqual(f1.vertices().unlazy(), f4.vertices().unlazy())

    def test_difference_probe(self):
        a = zencad.box(10)
        b = zencad.sphere(10)
        c = zencad.cone(5, 2, h=20)

        f1 = zencad.difference([a, b, c])
        f2 = a - b - c
        f3 = zencad.difference([c, a, b])
        f4 = c - a - b

        self.assertEqual(f1.vertices().unlazy(), f2.vertices().unlazy())
        self.assertEqual(f3.vertices().unlazy(), f4.vertices().unlazy())
