from OCP.gp import gp
from zencad.occ_compat import plane_xoy
from OCP.Geom import Geom_Line, Geom_Circle, Geom_Ellipse, Geom_BezierCurve, Geom_BSplineCurve
from OCP.GeomAPI import GeomAPI_Interpolate
from OCP.GeomAdaptor import GeomAdaptor_Curve

from zencad.opencascade_types import *
from zencad._eager import eager

from OCP.TColStd import TColStd_HArray1OfBoolean
import numpy
from zencad.util import *

from zencad.geom.transformable import Transformable
from zencad.geom.curve_algo import CurveAlgo


class Curve(CurveAlgo, Transformable):
    def __init__(self, crv):
        self._crv = crv

    def Curve(self):
        return self._crv

    def HCurveAdaptor(self):
        return self.AdaptorCurve()

    def edge(self, interval=None):
        import zencad.geom.wire
        return zencad.geom.wire.make_edge(self, interval)

    def _d0(self, arg):
        pnt = gp_Pnt()
        self._crv.D0(arg, pnt)
        return point3(pnt)

    def d0(self, arg):
        #adaptor = self.AdaptorCurve()
        pnt = gp_Pnt()  # , vec = gp_Pnt(), gp_Vec()
        self._crv.D0(arg, pnt)
        return point3(pnt)

    def transform(self, trsf):
        return Curve(self._crv.Transformed(trsf._trsf))

    def AdaptorCurve(self):
        return GeomAdaptor_Curve(self._crv)


class nocached_curve_generator:
    """Deprecated decorator marker for eager curve backends."""


def _line(pnt, dir) -> Curve:
    return Curve(Geom_Line(to_Pnt(pnt), to_Dir(dir)))


@eager.decorator(cls=nocached_curve_generator)
def line(pnt, dir) -> Curve:
    return _line(pnt, dir)


def _circle(radius) -> Curve:
    return Curve(Geom_Circle(plane_xoy(), radius))


@eager.decorator(cls=nocached_curve_generator)
def circle(radius) -> Curve:
    return _circle(radius)


def _ellipse(r1, r2) -> Curve:
    return Curve(Geom_Ellipse(plane_xoy(), r1, r2))


@eager.decorator(cls=nocached_curve_generator)
def ellipse(r1, r2) -> Curve:
    return _ellipse(r1, r2)


def _interpolate(pnts, tangs=None, closed=False):
    _pnts = opencascade_h_array1_of_pnt(pnts)
    algo = GeomAPI_Interpolate(_pnts, closed, 0.0000001)

    if tangs is not None:
        for i in range(len(tangs)):
            if tangs[i] is None:
                tangs[i] = vector3(0, 0, 0)

        if (len(tangs) != 0):
            _tangs = opencascade_array1_of_vec(tangs)

            _bools = TColStd_HArray1OfBoolean(1, len(tangs))
            for i in range(len(pnts)):
                _bools.SetValue(i + 1, bool(numpy.linalg.norm(tangs[i]) != 0))

            algo.Load(_tangs, _bools)

    algo.Perform()
    return Curve(algo.Curve())


@eager.decorator(cls=nocached_curve_generator)
def interpolate(pnts, tangs=None, closed=False):
    return _interpolate(pnts, tangs=tangs, closed=closed)


def _bezier(poles, weights=None):
    _poles = opencascade_array1_of_pnt(poles)
    if weights:
        _weights = opencascade_array1_of_real(weights)

    if weights:
        curve = Geom_BezierCurve(_poles, _weights)
    else:
        curve = Geom_BezierCurve(_poles)

    return Curve(curve)


@eager.decorator(cls=nocached_curve_generator)
def bezier(poles, weights=None):
    return _bezier(poles, weights=weights)


def _bspline(
        poles,
        knots,
        muls,
        degree: int,
        periodic: bool,
        weights=None,
        check_rational: bool = None
):
    _poles = opencascade_array1_of_pnt(poles)
    if weights:
        _weigths = opencascade_array1_of_real(weights)
    _knots = opencascade_array1_of_real(knots)
    _muls = opencascade_array1_of_int(muls)

    if weights:
        crv = Geom_BSplineCurve(
            _poles, _knots, _weigths, _muls,
            degree, periodic, check_rational)
    else:
        crv = Geom_BSplineCurve(
            _poles, _knots, _muls,
            degree, periodic)

    return Curve(crv)


@eager.decorator(cls=nocached_curve_generator)
def bspline(*args, **kwargs):
    return _bspline(*args, **kwargs)
