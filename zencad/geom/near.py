from OCC.Core.TopAbs import TopAbs_VERTEX, TopAbs_FACE, TopAbs_WIRE, TopAbs_EDGE, TopAbs_SOLID, TopAbs_SHELL, TopAbs_COMPOUND, TopAbs_COMPSOLID
from OCC.Core.TopExp import TopExp_Explorer
from OCC.Core.BRepExtrema import BRepExtrema_DistShapeShape

from zencad.geom.reflect_helpers import shape_types
from zencad.util import *

from zencad.geom.shape import Shape, shape_generator
from zencad.lazifier import *


def _near_part(shp, pnt, topabs):
    min = float("inf")
    ret = shape_types[topabs].construct()
    vtx = point3(pnt).Vtx()

    ex = TopExp_Explorer(shp.Shape(), topabs)
    while ex.More():
        obj = shape_types[topabs].convert(ex.Current())
        extrema = BRepExtrema_DistShapeShape(obj, vtx)

        if min > extrema.Value():
            ret = obj
            min = extrema.Value()

        ex.Next()

    return Shape(ret)


def _near_vertex(shp, pnt): return _near_part(shp, pnt, TopAbs_VERTEX)


def _near_edge(shp, pnt): return _near_part(shp, pnt, TopAbs_EDGE)


def _near_wire(shp, pnt): return _near_part(shp, pnt, TopAbs_WIRE)


def _near_face(shp, pnt): return _near_part(shp, pnt, TopAbs_FACE)


def _near_shell(shp, pnt): return _near_part(shp, pnt, TopAbs_SHELL)


def _near_solid(shp, pnt): return _near_part(shp, pnt, TopAbs_SOLID)


def _near_compsolid(shp, pnt): return _near_part(shp, pnt, TopAbs_COMPSOLID)


def _near_compound(shp, pnt): return _near_part(shp, pnt, TopAbs_COMPOUND)


@lazy.lazy(cls=shape_generator)
def near_vertex(shp, pnt): return _near_vertex(shp, pnt)


@lazy.lazy(cls=shape_generator)
def near_edge(shp, pnt): return _near_edge(shp, pnt)


@lazy.lazy(cls=shape_generator)
def near_wire(shp, pnt): return _near_wire(shp, pnt)


@lazy.lazy(cls=shape_generator)
def near_face(shp, pnt): return _near_face(shp, pnt)


@lazy.lazy(cls=shape_generator)
def near_shell(shp, pnt): return _near_shell(shp, pnt)


@lazy.lazy(cls=shape_generator)
def near_solid(shp, pnt): return _near_solid(shp, pnt)


@lazy.lazy(cls=shape_generator)
def near_compsolid(shp, pnt): return _near_compsolid(shp, pnt)


@lazy.lazy(cls=shape_generator)
def near_compound(shp, pnt): return _near_compound(shp, pnt)
