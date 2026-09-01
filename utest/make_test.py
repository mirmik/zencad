import unittest
import zencad


class MakeProbber(unittest.TestCase):
    def setUp(self):
        zencad.configure(cache_enabled=False)

    def test_make_wire(self):
        points = tuple(zencad.point3(*value) for value in ((0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0)))
        edges = tuple(zencad.segment(a, b) for a, b in zip(points, points[1:]))
        self.assertIsInstance(zencad.make_wire(edges), zencad.Wire)

    def test_make_face(self):
        points = tuple(zencad.point3(*value) for value in ((0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0)))
        edges = tuple(
            zencad.segment(a, b)
            for a, b in zip(points, (*points[1:], points[0]))
        )
        wire = zencad.make_wire(edges)
        self.assertIsInstance(zencad.fill(wire), zencad.Face)

    def test_make_shell(self):
        sphere = zencad.sphere(10)
        face = sphere.faces()[0]
        self.assertTrue(face.shapetype() == "face")
        self.assertIsInstance(zencad.make_shell([face]), zencad.Shell)
