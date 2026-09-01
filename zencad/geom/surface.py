from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
from OCP.Geom import Geom_CylindricalSurface
from OCP.gp import gp_Pnt, gp_Vec, gp_Ax3, gp_Dir

from zencad.util import point3, vector3
from zencad._eager import eager
from zencad.geom.curve import Curve
from zencad.occ_compat import build_curves_3d

from OCP.GeomFill import GeomFill_Sweep, GeomFill_Location
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeEdge

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
        build_curves_3d(edge)
        return Shape(edge)


class nocached_surface_generator:
    """Deprecated decorator marker for eager surface backends."""


def _cylinder(r):
    return Surface(Geom_CylindricalSurface(gp_Ax3(gp_Pnt(0, 0, 0), gp_Dir(0, 0, 1)), r))


@eager.decorator(cls=nocached_surface_generator)
def cylinder(r):
    return _cylinder(r)


def _sweep_surface(slaw, llaw, tol, cont, maxdegree, maxsegm):
    """Кинематическое построение поверхности по законам сечения и расположения"""

    algo = GeomFill_Sweep(llaw.Law())
    algo.SetTolerance(tol)
    algo.Build(slaw.Law(), GeomFill_Location, cont, maxdegree, maxsegm)

    return Surface(algo.Surface())
