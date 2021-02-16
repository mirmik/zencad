from OCC.Core.TopTools import TopTools_ListOfShape
from OCC.Core.BRepOffsetAPI import BRepOffsetAPI_MakeThickSolid, BRepOffsetAPI_MakeOffsetShape

from zencad.geom.near import _near_face
from zencad.shape import Shape, shape_generator
from zencad.lazy import *


def _thicksolid(proto, refs, t):
    facesToRemove = TopTools_ListOfShape()

    for p in refs:
        facesToRemove.Append(_near_face(proto, p).Face())

    algo = BRepOffsetAPI_MakeThickSolid()
    algo.MakeThickSolidByJoin(proto.Shape(), facesToRemove, t, 1.e-3)
    return Shape(algo.Shape())


@lazy.lazy(cls=shape_generator)
def thicksolid(proto, refs, t):
    return _thicksolid(proto, refs, t)


def _offset(shp, off):
    algo = BRepOffsetAPI_MakeOffsetShape()
    algo.PerformByJoin(shp.Shape(), off, 1e-6)
    algo.Build()
    return Shape(algo.Shape())


@lazy.lazy(cls=shape_generator)
def offset(*args, **kwargs):
    return _offset(*args, **kwargs)
