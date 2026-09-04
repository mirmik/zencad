import unittest
import zencad


class ReflectionProbber(unittest.TestCase):
    def setUp(self):
        zencad.configure(cache_enabled=False)

    def test_types_probe(self):
        m = zencad.box(10, 10, 10)

        self.assertEqual(m.faces()[0].shapetype(), "face")
        self.assertEqual(m.wires()[0].shapetype(), "wire")
        self.assertEqual(m.edges()[0].shapetype(), "edge")
        self.assertEqual(m.solids()[0].shapetype(), "solid")
