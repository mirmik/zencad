from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_MakeFace
from OCC.Core.Geom import Geom_CylindricalSurface
from OCC.Core.Geom2d import Geom2d_Ellipse, Geom2d_Curve
from OCC.Core.gp import gp_Pnt, gp_Vec, gp_Ax3, gp_Dir, gp_Ax2d, gp_Dir2d, gp_Pnt2d, gp_Trsf2d
from OCC.Core.Geom2d import Geom2d_TrimmedCurve
from OCC.Core.GCE2d import GCE2d_MakeSegment

from zencad.util import point3, vector3
from zencad.lazifier import *

import evalcache


class Curve2:
    def __init__(self, crv):
        self._crv = crv

    def Curve2(self):
        return self._crv

    def rotate(self, angle):
        trsf = gp_Trsf2d()
        trsf.SetRotation(gp_Pnt2d(0, 0), angle)
        return Curve2(Geom2d_Curve.DownCast(self._crv.Transformed(trsf)))

    def value(self, arg):
        return self.Curve2().Value(arg)


class nocached_curve2_generator(evalcache.LazyObject):
    """ Decorator for heavy functions.
            It use caching for lazy data restoring."""

    def __init__(self, *args, **kwargs):
        evalcache.LazyObject.__init__(self, *args, **kwargs)

    def __call__(self, *args, **kwargs):
        return self.lazyinvoke(
            self, args, kwargs,
            encache=False,
            decache=False,
            cls=evalcache.LazyObject
        )


def _ellipse(r1, r2):
    return Curve2(Geom2d_Ellipse(gp_Ax2d(gp_Pnt2d(0, 0), gp_Dir2d(1, 0)), r1, r2))


@lazy.lazy(cls=nocached_curve2_generator)
def ellipse(r1, r2):
    return _ellipse(r1, r2)


def _trimmed_curve2(crv, a, b):
    return Curve2(Geom2d_TrimmedCurve(crv.Curve2(), a, b))


@lazy.lazy(cls=nocached_curve2_generator)
def trimmed_curve2(crv, a, b):
    return _trimmed_curve2(crv, a, b)


def _segment(a, b):
    return Curve2(GCE2d_MakeSegment(a, b).Value())


@lazy.lazy(cls=nocached_curve2_generator)
def segment(a, b):
    return _segment(a, b)
