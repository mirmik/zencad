import unittest
import zencad


class Ops1d2dProbe(unittest.TestCase):
    def setUp(self):
        zencad.configure(cache_enabled=False)

    def test_fill(self):
        zencad.fill(zencad.circle(5, wire=True)).native()
        zencad.circle(5, wire=True).fill().native()

    def test_interpolate(self):
        points = tuple(
            zencad.point3(*value)
            for value in ((0, 0, 0), (1, 1, 0), (1, 1, 1))
        )
        tangents = tuple(
            zencad.vector3(*value)
            for value in ((0, 0, 0), (1, 0, 0), (0, 0, 1))
        )
        zencad.interpolate(points)
        zencad.interpolate(points, closed=True)
        zencad.interpolate(points, tangents)
        zencad.interpolate(points, tangents, closed=True)

    def test_sew(self):
        pnts = tuple(
            zencad.point3(*value)
            for value in ((0, 0, 0), (1, 1, 1), (1, 0, 0))
        )
        zencad.sew(
            [
                zencad.segment(pnts[0], pnts[1]),
                zencad.segment(pnts[1], pnts[2]),
                zencad.segment(pnts[2], pnts[0]),
            ]
        )

    def test_fillet2d(self):
        zencad.square(20).fillet2d(1)
        point = zencad.point3(0, 0, 0)
        zencad.square(20).fillet2d(1, [point])
        zencad.fillet2d(zencad.square(20), 1, [point])

    def test_chamfer2d(self):
        # not supported
        pass
