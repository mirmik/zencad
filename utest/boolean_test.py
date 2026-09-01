import unittest
import zencad


def rounded_list(a):
    return [round(f, 5) for f in a]


def lexsort(a):
    return sorted(
        tuple(round(value, 4) for value in vertex.point().value())
        for vertex in a
    )


class BooleanProbe(unittest.TestCase):
    def setUp(self):
        zencad.configure(cache_enabled=False)

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
