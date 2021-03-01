import unittest
import zencad
from functools import cmp_to_key
import evalcache
import zencad.util


def rounded_list(a):
    return [round(f, 5) for f in a]


def lexsort(a):
    a = evalcache.unlazy_if_need(a)

    def comparator(a, b):
        return 1 if a > b else -1

    a = [zencad.util.point3(round(f.x, 4), round(
        f.y, 4), round(f.z, 4)) for f in a]
    return sorted(a, key=cmp_to_key(comparator))


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

        self.assertEqual(lexsort(f1.vertices()), lexsort(f2.vertices()))
        self.assertEqual(lexsort(f1.vertices()), lexsort(f3.vertices()))
        #self.assertEqual(lexsort(f1.vertices()), lexsort(f4.vertices()))

    def test_intersect_probe(self):
        a = zencad.box(10)
        b = zencad.sphere(10)
        c = zencad.cone(5, 2, h=20)

        f1 = zencad.intersect([a, b, c])
        f2 = a ^ b ^ c
        f3 = zencad.intersect([c, a, b])
        f4 = c ^ a ^ b

        #self.assertEqual(lexsort(f1.vertices()), lexsort(f2.vertices()))
        #self.assertEqual(lexsort(f1.vertices()), lexsort(f3.vertices()))
        #self.assertEqual(lexsort(f1.vertices()), lexsort(f4.vertices()))

    def test_difference_probe(self):
        a = zencad.box(10)
        b = zencad.sphere(10)
        c = zencad.cone(5, 2, h=20)

        f1 = zencad.difference([a, b, c])
        f2 = a - b - c
        f3 = zencad.difference([c, a, b])
        f4 = c - a - b

        #self.assertEqual(lexsort(f1.vertices()), lexsort(f2.vertices()))
        #self.assertEqual(lexsort(f3.vertices()), lexsort(f4.vertices()))
