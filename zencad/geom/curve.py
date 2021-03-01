from zencad.curve import Curve, nocached_curve_generator

from OCC.Core.gp import gp
from OCC.Core.Geom import Geom_Line, Geom_Circle, Geom_Ellipse, Geom_BezierCurve, Geom_BSplineCurve
from OCC.Core.GeomAPI import GeomAPI_Interpolate

from zencad.opencascade_types import *
from zencad.lazifier import *

from OCC.Core.TColStd import TColStd_HArray1OfBoolean
import numpy
from zencad.util import *


def _line(pnt, dir) -> Curve:
    return Curve(Geom_Line(to_Pnt(pnt), to_Dir(dir)))


@lazy.lazy(cls=nocached_curve_generator)
def line(pnt, dir) -> Curve:
    return _line(pnt, dir)


def _circle(radius) -> Curve:
    return Curve(Geom_Circle(gp.XOY(), radius))


@lazy.lazy(cls=nocached_curve_generator)
def circle(radius) -> Curve:
    return _circle(radius)


def _ellipse(r1, r2) -> Curve:
    return Curve(Geom_Ellipse(gp.XOY(), r1, r2))


@lazy.lazy(cls=nocached_curve_generator)
def ellipse(r1, r2) -> Curve:
    return _ellipse(r1, r2)


def _interpolate(pnts, tang=None, closed=False):
    _pnts = opencascade_h_array1_of_pnt(pnts)
    algo = GeomAPI_Interpolate(_pnts, closed, 0.0000001)

    if tang is not None:
        for i in range(len(tang)):
            if tang[i] is None:
                tang[i] = vector3(0, 0, 0)

        if (len(tang) != 0):
            _tang = opencascade_array1_of_vec(tang)

            _bools = TColStd_HArray1OfBoolean(1, len(tang))
            for i in range(len(pnts)):
                _bools.SetValue(i + 1, bool(numpy.linalg.norm(tang[i]) != 0))

            algo.Load(_tang, _bools)

    algo.Perform()
    return Curve(algo.Curve())


@lazy.lazy(cls=nocached_curve_generator)
def interpolate(pnts, tang=None, closed=False):
    return _interpolate(pnts, tang=tang, closed=closed)


def _bezier(poles, weights=None):
    _poles = opencascade_array1_of_pnt(poles)
    if weights:
        _weights = opencascade_array1_of_real(weights)

    if weights:
        curve = Geom_BezierCurve(_poles, _weights)
    else:
        curve = Geom_BezierCurve(_poles)

    return Curve(curve)


@lazy.lazy(cls=nocached_curve_generator)
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


@lazy.lazy(cls=nocached_curve_generator)
def bspline(*args, **kwargs):
    return _bspline(*args, **kwargs)
