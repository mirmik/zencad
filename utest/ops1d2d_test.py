import unittest
import zencad


class Ops1d2dProbe(unittest.TestCase):
    def setUp(self):
        zencad.lazy.encache = False
        zencad.lazy.decache = False
        zencad.lazy.fastdo = True

    def test_fill(self):
        zencad.fill(zencad.circle(5, wire=True)).unlazy()
        zencad.circle(5, wire=True).fill().unlazy()

    def test_interpolate(self):
        zencad.interpolate([(0, 0, 0), (1, 1, 0), (1, 1, 1)])
        zencad.interpolate(pnts=[(0, 0, 0), (1, 1, 0), (1, 1, 1)], closed=True)
        zencad.interpolate(
            [(0, 0, 0), (1, 1, 0), (1, 1, 1)], [
                (0, 0, 0), (1, 1, 0), (1, 1, 1)]
        )
        zencad.interpolate(
            pnts=[(0, 0, 0), (1, 1, 0), (1, 1, 1)],
            tangs=[(0, 0, 0), (1, 0, 0), (0, 0, 1)],
            closed=True,
        )

    def test_sew(self):
        pnts = [(0, 0, 0), (1, 1, 1), (1, 0, 0)]
        zencad.sew(
            [
                zencad.segment(pnts[0], pnts[1]),
                zencad.segment(pnts[1], pnts[2]),
                zencad.segment(pnts[2], pnts[0]),
            ]
        )

    def test_fillet2d(self):
        zencad.square(20).fillet2d(1)
        zencad.square(20).fillet2d(r=1)
        zencad.fillet(proto=zencad.square(20), r=1)

        zencad.square(20).fillet2d(1, [(0, 0, 0)])
        zencad.square(20).fillet2d(refs=[(0, 0, 0)], r=1)
        zencad.fillet(proto=zencad.square(20), refs=[(0, 0, 0)], r=1)

    def test_chamfer2d(self):
        # not supported
        pass
