from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_MakeEdge
from OCC.Core.gp import gp_Pnt, gp_Vec

from zencad.util import point3

import evalcache


class Curve:
    def __init__(self, crv):
        self._crv = crv

    def Curve(self):
        return self._crv

    # TODO: Add unlazy wrapper
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


class nocached_curve_generator(evalcache.LazyObject):
    """	Decorator for heavy functions.
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
