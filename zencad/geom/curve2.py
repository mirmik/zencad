from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_MakeFace
from OCC.Core.Geom import Geom_CylindricalSurface
from OCC.Core.Geom2d import Geom2d_Ellipse
from OCC.Core.gp import gp_Pnt, gp_Vec, gp_Ax3, gp_Dir, gp_Ax2d, gp_Dir2d, gp_Pnt2d

from zencad.util import point3, vector3
from zencad.lazifier import *

import evalcache


class Curve2:
    def __init__(self, surf):
        self._surf = surf

    def Curve2(self):
        return self._surf


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


def _ellipse(r1, r2):
    return Curve2(Geom2d_Ellipse(gp_Ax2d(gp_Pnt2d(0, 0), gp_Dir2d(1, 0)), r1, r2))


@lazy.lazy(cls=nocached_surface_generator)
def ellipse(r1, r2):
    return _ellipse(r1, r2)
