import unittest
import zencad

class ReflectionProbber(unittest.TestCase):
    def setUp(self):
        zencad.lazy.encache = False
        zencad.lazy.decache = False
        zencad.lazy.fastdo = True

    def test_types_probe(self):
        m = zencad.box(10,10,10)

        self.assertEqual(m.faces()[0].shapetype().unlazy(), "face")
        self.assertEqual(m.wires()[0].shapetype().unlazy(), "wire")
        self.assertEqual(m.edges()[0].shapetype().unlazy(), "edge")
        self.assertEqual(m.solids()[0].shapetype().unlazy(), "solid")
