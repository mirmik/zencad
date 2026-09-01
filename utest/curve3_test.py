import unittest
import zencad
import numpy
import math


class Curve3(unittest.TestCase):
    def setUp(self):
        zencad.configure(cache_enabled=False)

    def test_api(self):
        points = (zencad.point3(0, 0, 0), zencad.point3(0, 0, 1))
        tangents = (zencad.vector3(0, 0, 1), zencad.vector3(0, 0, 1))
        a = zencad.interpolate_curve(points, tangents, closed=False)
        zencad.interpolate(points, closed=False)

        self.assertEqual(a.value(0), zencad.point3(0, 0, 0))
        self.assertEqual(a.value(1), zencad.point3(0, 0, 1))
        self.assertEqual(a.value(0.5), zencad.point3(0, 0, 0.5))

    def test_hadaptor(self):
        points = (zencad.point3(0, 0, 0), zencad.point3(0, 0, 1))
        curve = zencad.interpolate_curve(points, closed=False)
        self.assertIsNotNone(curve.HCurveAdaptor())


    def test_law_sweep(self):
        import zencad.geom.sweep_law as sl
        from zencad.geom.curve import Curve as LegacyCurve

        points = (zencad.point3(0, 0, 0), zencad.point3(0, 0, 1))
        curve = zencad.interpolate_curve(points, closed=False)
        crv = LegacyCurve(curve.native())
        trilaw = sl.law_corrected_frenet_trihedron()
        sl.law_spine_and_trihedron(crv, trilaw)

