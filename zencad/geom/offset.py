from OCC.Core.TopTools import TopTools_ListOfShape
from OCC.Core.BRepOffsetAPI import BRepOffsetAPI_MakeThickSolid, BRepOffsetAPI_MakeOffsetShape
from OCC.Core.ShapeFix import ShapeFix_Solid

from zencad.geom.near import _near_face
from zencad.geom.shape import Shape, shape_generator
from zencad.lazifier import *


def _thicksolid(proto, t, refs):
    facesToRemove = TopTools_ListOfShape()

    for p in refs:
        facesToRemove.Append(_near_face(proto, p).Face())

    algo = BRepOffsetAPI_MakeThickSolid()
    algo.MakeThickSolidByJoin(proto.Shape(), facesToRemove, t, 1.e-3)

    return Shape(algo.Shape())


@lazy.lazy(cls=shape_generator)
def thicksolid(proto, t, refs):
    return _thicksolid(proto, t, refs)


def _offset(shp, off):
    algo = BRepOffsetAPI_MakeOffsetShape()
    algo.PerformByJoin(shp.Shape(), off, 1e-6)
    algo.Build()
    return Shape(algo.Shape())


@lazy.lazy(cls=shape_generator)
def offset(*args, **kwargs):
    return _offset(*args, **kwargs)


def _shapefix_solid(shp):
    algo2 = ShapeFix_Solid(shp.Shape())
    algo2.Perform()
    return Shape(algo2.Solid())


@lazy.lazy(cls=shape_generator)
def shapefix_solid(shp):
    return _shapefix_solid(shp)
