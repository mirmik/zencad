import unittest
import zencad
import numpy
import math


class Curve3(unittest.TestCase):
    def setUp(self):
        zencad.lazy.encache = False
        zencad.lazy.decache = False
        zencad.lazy.fastdo = True

    def test_api(self):
        a = zencad.interpolate([(0, 0, 0), (0, 0, 1)], [
                               (0, 0, 1), (0, 0, 1)], closed=False)
        b = zencad.interpolate([(0, 0, 0), (0, 0, 1)], closed=False)

        self.assertEqual(a.value(0), zencad.point3(0, 0, 0))
        self.assertEqual(a.value(1), zencad.point3(0, 0, 1))
        self.assertEqual(a.value(0.5), zencad.point3(0, 0, 0.5))

    def test_hadaptor(self):
        a = zencad.interpolate([(0, 0, 0), (0, 0, 1)], [
                               (0, 0, 1), (0, 0, 1)], closed=False)
        crv = zencad.curve.Curve(a.Curve())
        hadaptor = crv.HCurveAdaptor()


    def test_law_sweep(self):
        import zencad.geom.sweep_law as sl
        a = zencad.interpolate([(0, 0, 0), (0, 0, 1)], [
                               (0, 0, 1), (0, 0, 1)], closed=False)        
        crv = zencad.curve.Curve(a.Curve())
        trilaw = sl.law_corrected_frenet_trihedron()
        sl.law_spine_and_trihedron(crv, trilaw)
    