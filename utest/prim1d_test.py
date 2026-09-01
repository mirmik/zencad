import unittest
import zencad


class Prim1dProbber(unittest.TestCase):
    def setUp(self):
        zencad.configure(cache_enabled=False)

    def test_segment_probe(self):
        zencad.segment(zencad.point3(0, 0, 0), zencad.point3(10, 20, 30))

    def test_polysegment_probe(self):
        pnts = self._points()
        zencad.polysegment(pnts, closed=False)
        zencad.polysegment(pnts, closed=True)

    def test_interpolate_probe(self):
        pnts = self._points()
        tangs = tuple(
            zencad.vector3(*value)
            for value in ((0, 0, 1), (1, 0, 0), (0, 1, 0), (0, 0, 0))
        )
        zencad.interpolate(pnts, closed=False)
        zencad.interpolate(pnts, closed=True)
        zencad.interpolate(pnts, tangs, closed=False)
        zencad.interpolate(pnts, tangs, closed=True)

    def test_circle_arc_probe(self):
        zencad.circle_arc(
            zencad.point3(0, 0),
            zencad.point3(1, 1),
            zencad.point3(1, 2),
        )

    def test_helix_probe(self):
        r = 20
        h = 20
        step = 2
        angle = zencad.deg(15)
        zencad.helix(r, h, step, left=True)
        zencad.helix(r, h, step, angle=angle, left=True)
        zencad.helix(r, h, step, left=False)
        zencad.helix(r, h, step, angle=angle, left=False)

    def test_bezier_probe(self):
        zencad.bezier(
            tuple(
                zencad.point3(*value)
                for value in ((0, 0, 0), (0, 1, 0), (1, 1, 0))
            )
        )

    @staticmethod
    def _points():
        return tuple(
            zencad.point3(*value)
            for value in ((0, 0, 0), (10, 20, 30), (10, 21, 35), (10, 22, 40))
        )
