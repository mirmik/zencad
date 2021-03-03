from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_MakeFace
from OCC.Core.Geom import Geom_CylindricalSurface
from OCC.Core.gp import gp_Pnt, gp_Vec, gp_Ax3, gp_Dir

from zencad.util import point3, vector3
from zencad.lazifier import *

import evalcache


class Surface:
    def __init__(self, surf):
        self._surf = surf

    def Surface(self):
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


def _cylinder(r):
    return Surface(Geom_CylindricalSurface(gp_Ax3(gp_Pnt(0, 0, 0), gp_Dir(0, 0, 1)), r))


@lazy.lazy(cls=nocached_surface_generator)
def cylinder(r):
    return _cylinder(r)
