from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_MakeFace
from OCC.Core.Geom import Geom_CylindricalSurface
from OCC.Core.gp import gp_Pnt, gp_Vec, gp_Ax3, gp_Dir

from zencad.util import point3, vector3
from zencad.lazifier import *
from zencad.geom.curve import Curve
from OCC.Core.BRepLib import breplib

from OCC.Core.GeomFill import GeomFill_Sweep, GeomFill_Location
from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_MakeEdge

import evalcache

from zencad.geom.shape import Shape


class Surface:
    def __init__(self, surf):
        self._surf = surf

    def Surface(self):
        return self._surf

    def v_iso_curve(self, parameter):
        return Curve(self.Surface().VIso(parameter))

    def u_iso_curve(self, parameter):
        return Curve(self.Surface().UIso(parameter))

    def urange(self):
        u1, u2, v1, v2 = self._surf.Bounds()
        return u1, u2

    def vrange(self):
        u1, u2, v1, v2 = self._surf.Bounds()
        return v1, v2

    def map(self, tcrv):
        mk = BRepBuilderAPI_MakeEdge(tcrv.Curve2(), self.Surface())
        edge = mk.Edge()
        breplib.BuildCurves3d(edge)
        return Shape(edge)


class nocached_surface_generator(evalcache.LazyObject):
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


def _cylinder(r):
    return Surface(Geom_CylindricalSurface(gp_Ax3(gp_Pnt(0, 0, 0), gp_Dir(0, 0, 1)), r))


@lazy.lazy(cls=nocached_surface_generator)
def cylinder(r):
    return _cylinder(r)


def _sweep_surface(slaw, llaw, tol, cont, maxdegree, maxsegm):
    """Кинематическое построение поверхности по законам сечения и расположения"""

    algo = GeomFill_Sweep(llaw.Law())
    algo.SetTolerance(tol)
    algo.Build(slaw.Law(), GeomFill_Location, cont, maxdegree, maxsegm)

    return Surface(algo.Surface())
